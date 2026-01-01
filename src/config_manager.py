"""Configuration manager for the application"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config.yaml"
        self.config: Dict[str, Any] = {}
        self.load_config()
        self._detect_android_sdk()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            # Default configuration
            self.config = {
                'android_sdk': {'root': '', 'emulator': '', 'adb': '', 'avd_manager': ''},
                'emulator': {
                    'hardware_acceleration': True,
                    'default_ram': 2048,
                    'default_vm_heap': 256,
                    'default_screen_density': 420,
                    'default_screen_resolution': '1080x1920'
                },
                'input_sync': {
                    'enabled': False,
                    'sync_touch': True,
                    'sync_keyboard': True,
                    'sync_scroll': True,
                    'delay_ms': 0
                },
                'ui': {
                    'theme': 'auto',
                    'auto_refresh_interval': 2,
                    'show_emulator_preview': True
                }
            }
            self.save_config()
    
    def save_config(self) -> None:
        """Save configuration to YAML file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def _detect_android_sdk(self) -> None:
        """Auto-detect Android SDK paths"""
        sdk_config = self.config.get('android_sdk', {})
        
        # Check environment variables
        sdk_root = (
            os.environ.get('ANDROID_SDK_ROOT') or 
            os.environ.get('ANDROID_HOME') or
            sdk_config.get('root', '')
        )
        
        if sdk_root and not sdk_config.get('root'):
            self.config.setdefault('android_sdk', {})['root'] = sdk_root
        
        sdk_root_path = Path(sdk_root) if sdk_root else None
        
        if sdk_root_path and sdk_root_path.exists():
            # Auto-detect tool paths
            platform_tools = sdk_root_path / "platform-tools"
            emulator_path = sdk_root_path / "emulator" / "emulator.exe"
            tools_bin = sdk_root_path / "cmdline-tools" / "latest" / "bin"
            
            if not sdk_config.get('adb') and (platform_tools / "adb.exe").exists():
                self.config['android_sdk']['adb'] = str(platform_tools / "adb.exe")
            
            if not sdk_config.get('emulator') and emulator_path.exists():
                self.config['android_sdk']['emulator'] = str(emulator_path)
            
            if not sdk_config.get('avd_manager'):
                # Try multiple possible locations for avdmanager
                for possible_path in [
                    tools_bin / "avdmanager.bat",
                    sdk_root_path / "tools" / "bin" / "avdmanager.bat",
                    sdk_root_path / "cmdline-tools" / "tools" / "bin" / "avdmanager.bat"
                ]:
                    if possible_path.exists():
                        self.config['android_sdk']['avd_manager'] = str(possible_path)
                        break
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'emulator.default_ram')"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
    
    @property
    def adb_path(self) -> Optional[str]:
        """Get ADB executable path"""
        return self.config.get('android_sdk', {}).get('adb')
    
    @property
    def emulator_path(self) -> Optional[str]:
        """Get emulator executable path"""
        return self.config.get('android_sdk', {}).get('emulator')
    
    @property
    def avd_manager_path(self) -> Optional[str]:
        """Get AVD manager executable path"""
        return self.config.get('android_sdk', {}).get('avd_manager')
