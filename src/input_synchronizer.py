"""Input synchronization module for syncing touch and keyboard input across emulators"""

import time
import subprocess
import threading
import queue
import ctypes
from ctypes import wintypes
from typing import List, Optional, Set, Dict, Tuple
from dataclasses import dataclass
import re
import sys
from concurrent.futures import ThreadPoolExecutor

# Import pynput (wrap in try-except to handle connection errors gently)
try:
    from pynput import mouse, keyboard
except ImportError:
    print("Warning: pynput not installed. Input sync will not work.")
    mouse = None
    keyboard = None

from .config_manager import ConfigManager
from .emulator_manager import EmulatorManager, EmulatorInstance

# Ctypes definitions for Windows
user32 = ctypes.windll.user32

def get_window_rect(hwnd):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect

def get_window_pid(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def get_foreground_window():
    return user32.GetForegroundWindow()

@dataclass
class DeviceResolution:
    width: int
    height: int

class InputSynchronizer:
    """Synchronizes input across multiple emulator instances using global hooks"""
    
    def __init__(self, config: ConfigManager, emulator_manager: EmulatorManager):
        self.config = config
        self.emulator_manager = emulator_manager
        self.sync_enabled = False
        self.synced_instances: Set[str] = set()
        
        # Threading for assignments
        self.action_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
        # Listeners
        self.mouse_listener = None
        self.key_listener = None
        
        # Concurrency
        self.executor = None
        
        # Cache
        self.resolutions: Dict[str, DeviceResolution] = {}
        self.window_info: Dict[str, int] = {} # instance_name -> hwnd (lazy update)
        self.last_press_info: Dict[mouse.Button, dict] = {} # Track button state for swipe

    def enable_sync(self, instance_names: List[str]) -> None:
        """Enable synchronization for specified instances"""
        self.synced_instances = set(instance_names)
        if not self.sync_enabled and self.synced_instances:
            if not self.executor:
                self.executor = ThreadPoolExecutor(max_workers=10)
            self._start_listening()
        self.sync_enabled = True
        
        # Prefetch resolutions
        for name in instance_names:
            self._get_device_resolution(name)

    def disable_sync(self) -> None:
        """Disable synchronization"""
        self.sync_enabled = False
        self.synced_instances.clear()
        self._stop_listening()
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

    def add_to_sync(self, instance_name: str) -> None:
        """Add an instance to synchronization group"""
        self.synced_instances.add(instance_name)
        if not self.sync_enabled:
            self.enable_sync(list(self.synced_instances))
        else:
            self._get_device_resolution(instance_name)

    def remove_from_sync(self, instance_name: str) -> None:
        """Remove an instance from synchronization group"""
        self.synced_instances.discard(instance_name)
        if not self.synced_instances:
            self.disable_sync()

    def _start_listening(self):
        """Start global input listeners"""
        if not mouse or not keyboard:
            return

        if not self.mouse_listener:
            self.mouse_listener = mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()
        
        if not self.key_listener:
            # We only listen for basic keys to avoid interfering with system
            self.key_listener = keyboard.Listener(on_release=self._on_key_release)
            self.key_listener.start()
            
            
    def _stop_listening(self):
        """Stop global input listeners"""
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except: pass
            self.mouse_listener = None
        if self.key_listener:
            try:
                self.key_listener.stop()
            except: pass
            self.key_listener = None

    def _get_active_instance_name(self) -> Optional[str]:
        """Get the name of the instance corresponding to the foreground window"""
        try:
            hwnd = get_foreground_window()
            pid = get_window_pid(hwnd)
            
            # Check our running instances
            for instance in self.emulator_manager.instances.values():
                if instance.pid == pid:
                    return instance.name
                
                # Also check for child processes (qemu often runs as child of emulator)
                try:
                    import psutil
                    parent = psutil.Process(instance.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        if child.pid == pid:
                            return instance.name
                except:
                    pass
        except Exception as e:
            print(f"DEBUG: Window check error: {e}")
            pass
        return None

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click and release for tap/swipe detection"""
        if not self.sync_enabled:
            return
            
        try:
            if pressed:
                # Track start of potential swipe
                instance_name = self._get_active_instance_name()
                if not instance_name or instance_name not in self.synced_instances:
                    return
                self.last_press_info[button] = {
                    'pos': (x, y),
                    'timestamp': time.time(),
                    'instance': instance_name
                }
            else:
                # Handle release (detect if it was a tap or swipe)
                if button not in self.last_press_info:
                    return
                
                press_data = self.last_press_info.pop(button)
                start_x, start_y = press_data['pos']
                instance_name = press_data['instance']
                
                # Check if we are still in the same instance
                current_instance = self._get_active_instance_name()
                if current_instance != instance_name:
                    return
                
                # Get window geometry to calculate relative position
                hwnd = get_foreground_window()
                rect = get_window_rect(hwnd)
                
                title_bar_height = 30 
                border_width = 8
                
                def to_rel(raw_x, raw_y):
                    rel_x = raw_x - rect.left - border_width
                    rel_y = raw_y - rect.top - title_bar_height
                    return rel_x, rel_y

                start_rel_x, start_rel_y = to_rel(start_x, start_y)
                end_rel_x, end_rel_y = to_rel(x, y)
                
                # Validation
                win_w = rect.right - rect.left - (border_width * 2)
                win_h = rect.bottom - rect.top - title_bar_height - border_width
                
                # Scale coordinates
                res = self._get_device_resolution(instance_name)
                if not res: return
                
                scale_x = res.width / win_w
                scale_y = res.height / win_h
                
                s_x, s_y = start_rel_x * scale_x, start_rel_y * scale_y
                e_x, e_y = end_rel_x * scale_x, end_rel_y * scale_y
                
                # Distinguish tap vs swipe (e.g. > 15 pixels movement)
                dist = ((e_x - s_x)**2 + (e_y - s_y)**2)**0.5
                if dist > 15:
                    duration_ms = max(100, int((time.time() - press_data['timestamp']) * 1000))
                    self.action_queue.put(('swipe', (s_x, s_y, e_x, e_y, duration_ms, instance_name)))
                else:
                    # It's a tap
                    # Note: Use start coordinates for tap to avoid slight jitter on click
                    self.action_queue.put(('touch', (s_x, s_y, instance_name)))
        except Exception:
            pass

    def _on_key_release(self, key):
        """Handle key release"""
        if not self.sync_enabled:
            return
            
        try:
            instance_name = self._get_active_instance_name()
            if not instance_name or instance_name not in self.synced_instances:
                return
            
            if hasattr(key, 'char'):
                char = key.char
                # Convert char to basic keycode if possible, or send as text
                # For simplicity, we'll try to map common keys
                keycode = self.get_keycode_from_key(char)
                if keycode:
                    self.action_queue.put(('key', (keycode, instance_name)))
            else:
                # Special keys
                key_name = key.name.upper()
                keycode = self.get_keycode_from_key(key_name)
                if keycode:
                    self.action_queue.put(('key', (keycode, instance_name)))
        except:
            pass

    def _process_queue(self):
        """Process actions in background thread"""
        while True:
            try:
                action_type, args = self.action_queue.get()
                
                if action_type == 'touch':
                    x, y, source_instance = args
                    self._send_touch_batch(x, y, source_instance)
                elif action_type == 'swipe':
                    sx, sy, ex, ey, duration, source_instance = args
                    self._send_swipe_batch(sx, sy, ex, ey, duration, source_instance)
                elif action_type == 'key':
                    keycode, source_instance = args
                    self._send_key_batch(keycode, source_instance)
                    
                self.action_queue.task_done()
            except Exception as e:
                # Reduce log spam
                # print(f"Sync worker error: {e}") 
                pass

    def _get_device_resolution(self, instance_name: str) -> Optional[DeviceResolution]:
        """Get device resolution via ADB"""
        if instance_name in self.resolutions:
            return self.resolutions[instance_name]
            
        instance = self.emulator_manager.get_instance(instance_name)
        if not instance or not instance.device_id:
            return None
            
        try:
            adb_path = self.config.adb_path
            # Check "input" size first? No, "wm size"
            result = subprocess.run(
                [adb_path, "-s", instance.device_id, "shell", "wm", "size"],
                capture_output=True, text=True, timeout=1
            )
            # Output: "Physical size: 1080x2400"
            match = re.search(r"size: (\d+)x(\d+)", result.stdout)
            if match:
                w, h = int(match.group(1)), int(match.group(2))
                res = DeviceResolution(w, h)
                self.resolutions[instance_name] = res
                return res
        except Exception:
            pass
        return None

    def _send_adb_cmd(self, device_id: str, cmd_args: List[str], delay_ms: float = 0):
        """Helper to send a single ADB command with optional delay"""
        try:
            adb_path = self.config.adb_path
            subprocess.run(
                [adb_path, "-s", device_id, "shell"] + cmd_args,
                capture_output=True, timeout=1
            )
            if delay_ms > 0:
                time.sleep(delay_ms)
        except Exception:
            pass

    def _send_touch_batch(self, x: float, y: float, exclude_instance: str):
        """Send touch to all synced instances in parallel"""
        if not self.executor: return
        
        delay_ms = self.config.get('input_sync.delay_ms', 0) / 1000.0
        
        for name in list(self.synced_instances):
            if name == exclude_instance:
                continue
                
            instance = self.emulator_manager.get_instance(name)
            if not instance or not instance.device_id:
                continue
            
            self.executor.submit(self._send_adb_cmd, instance.device_id, ["input", "tap", str(int(x)), str(int(y))], delay_ms)

    def _send_swipe_batch(self, sx, sy, ex, ey, duration, exclude_instance: str):
        """Send swipe to all synced instances in parallel"""
        if not self.executor: return
        
        delay_ms = self.config.get('input_sync.delay_ms', 0) / 1000.0
        
        for name in list(self.synced_instances):
            if name == exclude_instance:
                continue
            instance = self.emulator_manager.get_instance(name)
            if not instance or not instance.device_id:
                continue
            
            cmd = ["input", "swipe", str(int(sx)), str(int(sy)), str(int(ex)), str(int(ey)), str(duration)]
            self.executor.submit(self._send_adb_cmd, instance.device_id, cmd, delay_ms)

    def _send_key_batch(self, keycode: int, exclude_instance: str):
        """Send key to all synced instances in parallel"""
        if not self.executor: return
        
        delay_ms = self.config.get('input_sync.delay_ms', 0) / 1000.0
        
        for name in list(self.synced_instances):
            if name == exclude_instance:
                continue
            instance = self.emulator_manager.get_instance(name)
            if not instance or not instance.device_id:
                continue
            
            self.executor.submit(self._send_adb_cmd, instance.device_id, ["input", "keyevent", str(keycode)], delay_ms)

    def get_keycode_from_key(self, key: str) -> Optional[int]:
        """Convert key name/char to Android keycode"""
        keycode_map = {
            # Numbers
            '0': 7, '1': 8, '2': 9, '3': 10, '4': 11,
            '5': 12, '6': 13, '7': 14, '8': 15, '9': 16,
            # Letters
            'a': 29, 'b': 30, 'c': 31, 'd': 32, 'e': 33,
            'f': 34, 'g': 35, 'h': 36, 'i': 37, 'j': 38,
            'k': 39, 'l': 40, 'm': 41, 'n': 42, 'o': 43,
            'p': 44, 'q': 45, 'r': 46, 's': 47, 't': 48,
            'u': 49, 'v': 50, 'w': 51, 'x': 52, 'y': 53, 'z': 54,
            # Special keys
            'ENTER': 66, 'BACKSPACE': 67, 'SPACE': 62,
            'HOME': 3, 'BACK': 4, 'MENU': 82,
            'ESC': 111,
            'UP': 19, 'DOWN': 20, 'LEFT': 21, 'RIGHT': 22,
        }
        return keycode_map.get(key.lower() if len(key) == 1 else key.upper())
