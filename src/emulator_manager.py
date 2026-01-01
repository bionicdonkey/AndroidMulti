"""Android emulator management module"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .config_manager import ConfigManager
from .logger import get_logger


class EmulatorState(Enum):
    """Emulator state enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    CRASHED = "crashed"
    UNKNOWN = "unknown"


@dataclass
class EmulatorInstance:
    """Represents an Android emulator instance"""
    name: str
    avd_name: str
    port: int
    state: EmulatorState
    pid: Optional[int] = None
    device_id: Optional[str] = None
    created_from: Optional[str] = None  # Original AVD name if cloned
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['state'] = self.state.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmulatorInstance':
        """Create from dictionary"""
        data['state'] = EmulatorState(data.get('state', 'unknown'))
        return cls(**data)


class EmulatorManager:
    """Manages Android emulator instances"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = get_logger()
        self.instances: Dict[str, EmulatorInstance] = {}
        self._next_port = 5554
        self._avd_dir = Path.home() / ".android" / "avd"
        self._state_file = Path.home() / ".android_multi_emulator" / "instances.json"
        self._load_instances()
    
    def _run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command and return returncode, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            stdout = result.stdout if capture_output else ""
            stderr = result.stderr if capture_output else ""
            return result.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def _load_instances(self) -> None:
        """Load saved instances from disk"""
        if not self._state_file.exists():
            self.logger.debug("No saved instances file found")
            return
        
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for instance_data in data.get('instances', []):
                try:
                    instance = EmulatorInstance.from_dict(instance_data)
                    # Mark all loaded instances as stopped initially
                    # They'll be updated by refresh_instances if still running
                    instance.state = EmulatorState.STOPPED
                    instance.pid = None
                    self.instances[instance.name] = instance
                    self.logger.debug(f"Loaded saved instance: {instance.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to load instance from saved data: {e}")
            
            self.logger.info(f"Loaded {len(self.instances)} saved instance(s)")
        except Exception as e:
            self.logger.error(f"Failed to load instances from {self._state_file}: {e}")
    
    def _save_instances(self) -> None:
        """Save current instances to disk"""
        try:
            # Ensure directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert instances to dict
            data = {
                'instances': [inst.to_dict() for inst in self.instances.values()]
            }
            
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(self.instances)} instance(s) to {self._state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save instances to {self._state_file}: {e}")
    
    def list_avds(self) -> List[Dict[str, str]]:
        """List available AVD templates"""
        avd_manager = self.config.avd_manager_path
        if not avd_manager or not Path(avd_manager).exists():
            return []
        
        returncode, stdout, stderr = self._run_command([avd_manager, "list", "avd"])
        
        if returncode != 0:
            return []
        
        avds = []
        current_avd = {}
        
        for line in stdout.split('\n'):
            line = line.strip()
            if line.startswith('Name:'):
                if current_avd:
                    avds.append(current_avd)
                current_avd = {'name': line.replace('Name:', '').strip()}
            elif line.startswith('Path:'):
                current_avd['path'] = line.replace('Path:', '').strip()
            elif line.startswith('Target:'):
                current_avd['target'] = line.replace('Target:', '').strip()
            elif line.startswith('API Level:'):
                current_avd['api_level'] = line.replace('API Level:', '').strip()
        
        if current_avd:
            avds.append(current_avd)
        
        return avds
    
    def create_clone_avd(self, source_avd: str, clone_name: str) -> bool:
        """Create a cloned AVD from an existing one with proper independence"""
        import shutil
        import uuid
        import hashlib
        
        avd_manager = self.config.avd_manager_path
        if not avd_manager:
            self.logger.error("AVD Manager path not configured")
            return False
        
        # First, get the source AVD path
        source_avd_path = self._avd_dir / f"{source_avd}.avd"
        source_ini_path = self._avd_dir / f"{source_avd}.ini"
        
        if not source_avd_path.exists():
            self.logger.error(f"Source AVD directory not found: {source_avd_path}")
            return False
        
        if not source_ini_path.exists():
            self.logger.error(f"Source AVD ini file not found: {source_ini_path}")
            return False
        
        clone_avd_path = self._avd_dir / f"{clone_name}.avd"
        clone_ini_path = self._avd_dir / f"{clone_name}.ini"
        
        try:
            self.logger.info(f"Creating clone AVD '{clone_name}' from '{source_avd}'")
            
            # Remove existing clone if it exists
            if clone_avd_path.exists():
                self.logger.warning(f"Removing existing clone directory: {clone_avd_path}")
                shutil.rmtree(clone_avd_path)
            if clone_ini_path.exists():
                clone_ini_path.unlink()
            
            # Copy AVD directory, ignoring lock files and temporary files
            self.logger.debug(f"Copying AVD directory from {source_avd_path} to {clone_avd_path}")
            
            def ignore_lock_files(directory, files):
                """Ignore lock files and temporary files during copy"""
                ignore_patterns = [
                    'multiinstance.lock',
                    '*.lock',
                    'hardware-qemu.ini.lock',
                    'userdata-qemu.img.lock'
                ]
                ignored = []
                for file in files:
                    for pattern in ignore_patterns:
                        if pattern.startswith('*'):
                            # Wildcard pattern
                            if file.endswith(pattern[1:]):
                                ignored.append(file)
                                break
                        else:
                            # Exact match
                            if file == pattern:
                                ignored.append(file)
                                break
                if ignored:
                    self.logger.debug(f"Ignoring files during copy: {ignored}")
                return ignored
            
            shutil.copytree(source_avd_path, clone_avd_path, ignore=ignore_lock_files)
            
            # Remove snapshots directory to prevent conflicts
            snapshots_dir = clone_avd_path / "snapshots"
            if snapshots_dir.exists():
                self.logger.debug(f"Removing snapshots directory: {snapshots_dir}")
                shutil.rmtree(snapshots_dir)
            
            # Remove QCOW2 overlay files that shouldn't be shared between clones
            # Keep base .img files as the emulator needs them
            cache_files_to_remove = [
                "cache.img.qcow2",
                "userdata-qemu.img.qcow2",
                "sdcard.img.qcow2",
                "system.img.qcow2"
            ]
            for cache_file in cache_files_to_remove:
                cache_path = clone_avd_path / cache_file
                if cache_path.exists():
                    self.logger.debug(f"Removing overlay file: {cache_file}")
                    cache_path.unlink()
            
            # Generate unique identifiers for the clone
            unique_id = str(uuid.uuid4())
            device_hash = hashlib.md5(clone_name.encode()).hexdigest()
            
            # Update config.ini with unique identifiers
            config_ini = clone_avd_path / "config.ini"
            if config_ini.exists():
                self.logger.debug("Updating config.ini with unique identifiers")
                content = config_ini.read_text(encoding='utf-8')
                lines = content.split('\n')
                updated_lines = []
                avd_name_updated = False
                avd_id_updated = False
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('avd.name'):
                        updated_lines.append(f'avd.name={clone_name}')
                        avd_name_updated = True
                    elif stripped.startswith('AvdId'):
                        updated_lines.append(f'AvdId={clone_name}')
                        avd_id_updated = True
                    elif stripped.startswith('hw.device.hash2'):
                        updated_lines.append(f'hw.device.hash2={device_hash}')
                    else:
                        updated_lines.append(line)
                
                # Add missing entries if not found
                if not avd_name_updated:
                    updated_lines.append(f'avd.name={clone_name}')
                if not avd_id_updated:
                    updated_lines.append(f'AvdId={clone_name}')
                
                config_ini.write_text('\n'.join(updated_lines), encoding='utf-8')
            else:
                self.logger.warning(f"config.ini not found in {clone_avd_path}")
            
            # Delete hardware-qemu.ini to force regeneration
            # This is safer than patching it because the emulator will regenerate it
            # with the correct paths for the new AVD on first boot
            hardware_ini = clone_avd_path / "hardware-qemu.ini"
            if hardware_ini.exists():
                self.logger.debug(f"Removing hardware-qemu.ini from clone to force regeneration: {hardware_ini}")
                hardware_ini.unlink()
            
            # Copy and update .ini file
            self.logger.debug(f"Creating clone ini file: {clone_ini_path}")
            content = source_ini_path.read_text(encoding='utf-8')
            
            # Update path to point to clone directory
            path_str = str(clone_avd_path).replace('\\', '/')
            lines = content.split('\n')
            updated_lines = []
            path_updated = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('path=') or stripped.startswith('path '):
                    updated_lines.append(f'path={path_str}')
                    path_updated = True
                elif stripped.startswith('path.rel'):
                    # Ignore path.rel to force usage of absolute path, avoiding "Same AVD" errors
                    continue
                elif stripped.startswith('target'):
                    updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add path if not found
            if not path_updated:
                updated_lines.append(f'path={path_str}')
            
            clone_ini_path.write_text('\n'.join(updated_lines), encoding='utf-8')
            
            self.logger.info(f"Successfully cloned AVD '{source_avd}' to '{clone_name}'")
            self.logger.info(f"Clone location: {clone_avd_path}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Error creating clone AVD '{source_avd}' to '{clone_name}': {e}")
            # Clean up partial clone on failure
            try:
                if clone_avd_path.exists():
                    shutil.rmtree(clone_avd_path)
                if clone_ini_path.exists():
                    clone_ini_path.unlink()
            except:
                pass
            return False
    
    def start_emulator(self, avd_name: str, instance_name: Optional[str] = None, 
                      port: Optional[int] = None, use_readonly: Optional[bool] = None) -> Optional[EmulatorInstance]:
        """Start an emulator instance"""
        emulator_path = self.config.emulator_path
        if not emulator_path or not Path(emulator_path).exists():
            self.logger.error(f"Cannot start emulator: emulator path not configured or invalid: {emulator_path}")
            return None
        
        instance_name = instance_name or f"{avd_name}_{int(time.time())}"
        port = port or self._get_next_port()
        device_id = f"emulator-{port}"
        
        # Create instance
        instance = EmulatorInstance(
            name=instance_name,
            avd_name=avd_name,
            port=port,
            state=EmulatorState.STARTING,
            device_id=device_id
        )
        
        # Clear any stale locks before starting
        self._clear_locks(avd_name)
        
        # Determine if we need -read-only flag
        # Only use it if explicitly requested or if same AVD is running without cloning
        if use_readonly is None:
            running_instances = [inst for inst in self.instances.values() 
                               if inst.state == EmulatorState.RUNNING]
            # Check if the exact same AVD name is already running (not a clone)
            same_avd_running = any(inst.avd_name == avd_name for inst in running_instances)
            use_readonly = same_avd_running  # Only use read-only if same AVD (not clone) is running
        
        # Build emulator command
        cmd = [
            emulator_path,
            f"@{avd_name}",
            "-port", str(port),
            "-no-snapshot-load",  # Always start fresh
        ]
        
        # Add -read-only flag if needed (allows multiple instances of same AVD)
        # WARNING: This makes the emulator read-only - no data persistence!
        if use_readonly:
            cmd.append("-read-only")
            self.logger.warning(f"Using -read-only flag for '{avd_name}' - data will not persist!")
        
        # Add hardware acceleration if enabled
        if self.config.get('emulator.hardware_acceleration', True):
            # Try to detect available acceleration
            accel_mode = self._detect_acceleration_mode()
            if accel_mode:
                cmd.extend(["-accel", accel_mode])
            else:
                cmd.extend(["-accel", "on"])  # Let emulator choose
        
        # Windows-specific optimizations
        cmd.extend([
            "-gpu", "auto",  # Auto-select GPU mode
            "-memory", str(self.config.get('emulator.default_ram', 2048)),
        ])
        
        # Start emulator in background
        try:
            self.logger.info(f"Starting emulator '{instance_name}' on port {port} with command: {' '.join(cmd[:3])}...")
            
            # Create log file for emulator output
            log_dir = Path.home() / ".android_multi_emulator" / "emulator_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{instance_name}_{port}.log"
            
            with open(log_file, 'w', encoding='utf-8') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,  # Merge stderr to stdout
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            
            # Give the process a moment to start and check if it's still running
            time.sleep(0.5)
            
            # Check if process is still running
            try:
                return_code = process.poll()
                if return_code is not None:
                    # Process already exited - read the log to see why
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8') as f:
                            error_output = f.read()
                            if error_output:
                                self.logger.error(f"Emulator '{instance_name}' exited immediately (return code: {return_code}). Error output:\n{error_output[:1000]}")
                            else:
                                self.logger.error(f"Emulator '{instance_name}' exited immediately with return code {return_code} (no error output)")
                    else:
                        self.logger.error(f"Emulator '{instance_name}' exited immediately with return code {return_code} (log file not created)")
                    return None
            except ProcessLookupError:
                # Process doesn't exist anymore
                self.logger.error(f"Emulator '{instance_name}' process (PID {process.pid}) not found after start")
                return None
            
            instance.pid = process.pid
            self.logger.info(f"Emulator '{instance_name}' process started with PID {process.pid} (log: {log_file})")
        except Exception as e:
            self.logger.exception(f"Error starting emulator '{instance_name}': {e}")
            return None
        
        self.instances[instance_name] = instance
        self._save_instances()  # Persist the new instance
        return instance
    
    def _detect_acceleration_mode(self) -> Optional[str]:
        """Detect if hardware acceleration is available
        
        Returns 'on' if acceleration is available, 'auto' otherwise.
        The emulator only accepts: on, off, auto for -accel parameter.
        """
        import platform
        
        if platform.system() != "Windows":
            return "on"
        
        # Check for Hyper-V (Windows Hypervisor Platform)
        # or HAXM - if either is available, use 'on'
        try:
            result = subprocess.run(
                ["systeminfo"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Hyper-V" in result.stdout or "Windows Hypervisor Platform" in result.stdout:
                self.logger.debug("Detected Windows Hypervisor Platform (WHPX)")
                return "on"  # WHPX is available
        except:
            pass
        
        # Check for HAXM (legacy)
        try:
            result = subprocess.run(
                ["sc", "query", "intelhaxm"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if "RUNNING" in result.stdout:
                self.logger.debug("Detected Intel HAXM")
                return "on"  # HAXM is available
        except:
            pass
        
        # Default to auto-detection - let emulator choose
        self.logger.debug("Using auto-detection for hardware acceleration")
        return "auto"
    
    def _get_next_port(self) -> int:
        """Get the next available emulator port"""
        used_ports = {inst.port for inst in self.instances.values()}
        port = self._next_port
        while port in used_ports or port % 2 != 0:
            port += 2  # Emulator ports must be even
        self._next_port = port + 2
        return port
    
    def stop_emulator(self, instance_name: str) -> bool:
        """Stop an emulator instance"""
        instance = self.instances.get(instance_name)
        if not instance:
            self.logger.warning(f"Cannot stop emulator '{instance_name}': instance not found")
            return False
        
        self.logger.info(f"Stopping emulator '{instance_name}' (PID: {instance.pid})")
        
        adb_path = self.config.adb_path
        if adb_path and instance.device_id:
            # Try graceful shutdown via ADB
            self.logger.debug(f"Sending ADB kill command to {instance.device_id}")
            self._run_command([adb_path, "-s", instance.device_id, "emu", "kill"])
        
        # Force kill if still running
        if instance.pid:
            try:
                import psutil
                process = psutil.Process(instance.pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                    self.logger.debug(f"Emulator process {instance.pid} terminated gracefully")
                except psutil.TimeoutExpired:
                    process.kill()
                    self.logger.debug(f"Emulator process {instance.pid} force killed")
            except psutil.NoSuchProcess:
                self.logger.debug(f"Emulator process {instance.pid} already terminated")
            except psutil.AccessDenied:
                self.logger.warning(f"Access denied when trying to stop process {instance.pid}")
        
        instance.state = EmulatorState.STOPPED
        instance.pid = None  # Clear PID since it's no longer running
        # Keep instance in dictionary so it persists and can be restarted
        self._save_instances()  # Persist the state change
        self.logger.info(f"Emulator '{instance_name}' stopped successfully")
        return True
    
    def refresh_instances(self) -> None:
        """Refresh emulator instance states and discover new running emulators"""
        adb_path = self.config.adb_path
        if not adb_path:
            return
        
        # Get list of running emulators from ADB
        returncode, stdout, _ = self._run_command([adb_path, "devices", "-l"])
        
        if returncode != 0:
            return
        
        running_devices = {}
        device_details = {}  # port -> {device_id, model, etc}
        
        for line in stdout.split('\n')[1:]:  # Skip header
            if 'emulator-' in line and 'device' in line:
                # Extract device ID and port
                match = re.search(r'emulator-(\d+)', line)
                if match:
                    port = int(match.group(1))
                    device_id = f"emulator-{port}"
                    running_devices[port] = device_id
                    
                    # Try to extract AVD name from the line
                    avd_match = re.search(r'model:(\S+)', line)
                    device_details[port] = {'device_id': device_id}
        
        # Update instance states for known instances
        for instance in list(self.instances.values()):
            if instance.port in running_devices:
                instance.state = EmulatorState.RUNNING
                instance.device_id = running_devices[instance.port]
            elif instance.state == EmulatorState.STARTING:
                # Still starting, keep as starting for now
                pass
            else:
                # Instance stopped - remove from tracking if it was stopped
                # But keep it if it might restart
                instance.state = EmulatorState.STOPPED
        
        # Discover new running emulators that aren't in our instances
        known_ports = {inst.port for inst in self.instances.values()}
        for port, device_id in running_devices.items():
            if port not in known_ports:
                # New emulator found - try to get AVD name from emulator
                # For now, create a generic instance name
                try:
                    # Try to get AVD name via ADB shell
                    returncode, output, _ = self._run_command([
                        adb_path, "-s", device_id, "shell", "getprop", "ro.kernel.qemu.avd_name"
                    ])
                    if returncode == 0 and output.strip():
                        avd_name = output.strip()
                    else:
                        # Fallback: try to infer from device model or use generic name
                        avd_name = f"unknown_avd_{port}"
                except:
                    avd_name = f"unknown_avd_{port}"
                
                # Create instance for discovered emulator
                instance_name = f"{avd_name}_{port}"
                new_instance = EmulatorInstance(
                    name=instance_name,
                    avd_name=avd_name,
                    port=port,
                    state=EmulatorState.RUNNING,
                    device_id=device_id
                )
                self.instances[instance_name] = new_instance
                self.logger.info(f"Discovered running emulator on port {port}: {instance_name}")
    
    def get_instance(self, instance_name: str) -> Optional[EmulatorInstance]:
        """Get an emulator instance by name"""
        return self.instances.get(instance_name)
    
    def list_instances(self) -> List[EmulatorInstance]:
        """List all emulator instances"""
        return list(self.instances.values())
    
    def create_and_start_clone(self, source_avd: str, clone_name: Optional[str] = None) -> Optional[EmulatorInstance]:
        """Create a clone AVD and start it"""
        clone_name = clone_name or f"{source_avd}_clone_{int(time.time())}"
        
        # Create clone AVD
        if not self.create_clone_avd(source_avd, clone_name):
            return None
        
        # Start the cloned emulator (clones shouldn't need -read-only since they're different AVDs)
        return self.start_emulator(clone_name, instance_name=clone_name, use_readonly=False)
    
    def get_avd_dir(self, avd_name: str) -> Path:
        """Get the directory path for an AVD"""
        # Usually ~/.android/avd/Name.avd
        if avd_name.endswith('.avd'):
            return self._avd_dir / avd_name
        return self._avd_dir / f"{avd_name}.avd"
    
    def rename_instance(self, old_name: str, new_name: str) -> bool:
        """Rename an emulator instance"""
        instance = self.instances.get(old_name)
        if not instance:
            self.logger.warning(f"Cannot rename instance '{old_name}': instance not found")
            return False
        
        if new_name in self.instances:
            self.logger.warning(f"Cannot rename to '{new_name}': name already exists")
            return False
        
        if not new_name or not new_name.strip():
            self.logger.warning(f"Cannot rename to empty name")
            return False
        
        # Update the instance name
        instance.name = new_name
        self.instances[new_name] = instance
        del self.instances[old_name]
        
        # Persist the change
        self._save_instances()
        self.logger.info(f"Renamed instance '{old_name}' to '{new_name}'")
        return True
    
    def delete_instance(self, instance_name: str, delete_avd: bool = True) -> bool:
        """Permanently delete an instance and optionally its AVD files"""
        instance = self.instances.get(instance_name)
        if not instance:
            self.logger.warning(f"Cannot delete instance '{instance_name}': instance not found")
            return False
        
        # Stop the emulator if it's running
        if instance.state == EmulatorState.RUNNING:
            self.stop_emulator(instance_name)
        
        # Delete the AVD files if requested and if it's a clone
        if delete_avd and instance.avd_name:
            avd_path = self._avd_dir / f"{instance.avd_name}.avd"
            ini_path = self._avd_dir / f"{instance.avd_name}.ini"
            
            try:
                if avd_path.exists():
                    import shutil
                    shutil.rmtree(avd_path)
                    self.logger.info(f"Deleted AVD directory: {avd_path}")
                
                if ini_path.exists():
                    ini_path.unlink()
                    self.logger.info(f"Deleted AVD ini file: {ini_path}")
            except Exception as e:
                self.logger.error(f"Error deleting AVD files for '{instance_name}': {e}")
                return False
        
        # Remove from instances dictionary
        del self.instances[instance_name]
        self._save_instances()
        self.logger.info(f"Deleted instance '{instance_name}'")
        return True
    
    def _clear_locks(self, avd_name: str) -> None:
        """Clear any stale lock files for an AVD"""
        try:
            avd_path = self._avd_dir / f"{avd_name}.avd"
            if not avd_path.exists():
                return
            
            lock_patterns = [
                'multiinstance.lock',
                'hardware-qemu.ini.lock',
                'userdata-qemu.img.lock'
            ]
            
            for pattern in lock_patterns:
                lock_file = avd_path / pattern
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        self.logger.debug(f"Removed stale lock file: {lock_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove lock file {lock_file}: {e}")
                        
            # Also check for .lock directories (some emulators use these)
            for item in avd_path.glob("*.lock"):
                try:
                    if item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    self.logger.debug(f"Removed stale lock: {item}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove lock {item}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error clearing locks for {avd_name}: {e}")

