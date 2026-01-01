#!/usr/bin/env python3
"""
Android SDK Detection and Setup Utility

Detects and optionally installs Android SDK and related tools.
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Tuple


class AndroidSDKManager:
    """Manages Android SDK detection and setup"""

    def __init__(self):
        self.system = platform.system()
        self.sdk_root = None
        self.adb_path = None
        self.emulator_path = None
        self.avdmanager_path = None

    def find_sdk_root(self) -> Optional[Path]:
        """Find Android SDK root directory"""
        # Check environment variables
        for env_var in ['ANDROID_SDK_ROOT', 'ANDROID_HOME']:
            sdk_path = os.environ.get(env_var)
            if sdk_path and Path(sdk_path).exists():
                return Path(sdk_path)

        # Check standard installation locations
        standard_paths = self._get_standard_sdk_paths()
        for path in standard_paths:
            if path.exists():
                return path

        return None

    def _get_standard_sdk_paths(self) -> list:
        """Get standard SDK installation paths based on OS"""
        if self.system == "Windows":
            username = os.environ.get("USERNAME", "")
            return [
                Path(f"C:\\Users\\{username}\\AppData\\Local\\Android\\Sdk"),
                Path("C:\\Android\\sdk"),
            ]
        elif self.system == "Darwin":  # macOS
            return [
                Path.home() / "Library" / "Android" / "sdk",
                Path("/usr/local/opt/android-sdk"),
            ]
        else:  # Linux
            return [
                Path.home() / "Android" / "Sdk",
                Path.home() / ".android" / "sdk",
                Path("/opt/android-sdk"),
            ]

    def check_tool(self, tool_name: str, tool_path: Optional[Path] = None) -> Tuple[bool, Optional[Path]]:
        """Check if a tool exists and is executable"""
        if tool_path:
            if tool_path.exists():
                return True, tool_path
            return False, None

        if not self.sdk_root:
            return False, None

        # Determine tool location based on OS and tool name
        if self.system == "Windows":
            tool_locations = self._get_tool_paths_windows(tool_name)
        elif self.system == "Darwin":
            tool_locations = self._get_tool_paths_unix(tool_name)
        else:  # Linux
            tool_locations = self._get_tool_paths_unix(tool_name)

        for location in tool_locations:
            if location.exists():
                return True, location
        return False, None

    def _get_tool_paths_windows(self, tool_name: str) -> list:
        """Get Windows tool paths"""
        paths = []
        if tool_name == "adb":
            paths = [self.sdk_root / "platform-tools" / "adb.exe"]
        elif tool_name == "emulator":
            paths = [self.sdk_root / "emulator" / "emulator.exe"]
        elif tool_name == "avdmanager":
            paths = [
                self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat",
                self.sdk_root / "tools" / "bin" / "avdmanager.bat",
            ]
        return paths

    def _get_tool_paths_unix(self, tool_name: str) -> list:
        """Get Unix/Linux/macOS tool paths"""
        paths = []
        if tool_name == "adb":
            paths = [self.sdk_root / "platform-tools" / "adb"]
        elif tool_name == "emulator":
            paths = [self.sdk_root / "emulator" / "emulator"]
        elif tool_name == "avdmanager":
            paths = [
                self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager",
                self.sdk_root / "tools" / "bin" / "avdmanager",
            ]
        return paths

    def verify_sdk_installation(self) -> Dict[str, bool]:
        """Verify all required SDK components"""
        self.sdk_root = self.find_sdk_root()

        results = {
            "sdk_found": self.sdk_root is not None,
            "adb": False,
            "emulator": False,
            "avdmanager": False,
        }

        if not self.sdk_root:
            return results

        # Check for each tool
        results["adb"], self.adb_path = self.check_tool("adb")
        results["emulator"], self.emulator_path = self.check_tool("emulator")
        results["avdmanager"], self.avdmanager_path = self.check_tool("avdmanager")

        return results

    def get_adb_version(self) -> Optional[str]:
        """Get ADB version"""
        if not self.adb_path:
            return None

        try:
            result = subprocess.run(
                [str(self.adb_path), "version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Extract version from first line
            if result.stdout:
                return result.stdout.split("\n")[0]
        except Exception:
            pass

        return None

    def print_status(self):
        """Print SDK installation status"""
        results = self.verify_sdk_installation()

        print("\n" + "=" * 50)
        print("Android SDK Status")
        print("=" * 50)

        if results["sdk_found"]:
            print(f"✓ SDK Root: {self.sdk_root}")
        else:
            print("✗ Android SDK not found")
            print(f"  Looked in: {', '.join(str(p) for p in self._get_standard_sdk_paths())}")

        if results["adb"]:
            print(f"✓ ADB: {self.adb_path}")
            adb_version = self.get_adb_version()
            if adb_version:
                print(f"  Version: {adb_version}")
        else:
            print("✗ ADB not found")

        if results["emulator"]:
            print(f"✓ Emulator: {self.emulator_path}")
        else:
            print("✗ Emulator not found")

        if results["avdmanager"]:
            print(f"✓ AVD Manager: {self.avdmanager_path}")
        else:
            print("✗ AVD Manager not found")

        print("=" * 50 + "\n")

        return results

    def get_sdk_setup_instructions(self) -> str:
        """Get instructions for setting up Android SDK"""
        if self.system == "Windows":
            return self._get_windows_instructions()
        elif self.system == "Darwin":
            return self._get_macos_instructions()
        else:
            return self._get_linux_instructions()

    def _get_windows_instructions(self) -> str:
        return """
Android SDK Setup Instructions (Windows)
=========================================

1. Download Android SDK Command-line Tools:
   - Visit: https://developer.android.com/studio/command-line-tools
   - Download the Windows version

2. Extract to: C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk
   (Create the folder if it doesn't exist)

3. Add to PATH:
   - Open System Properties → Environment Variables
   - Add: C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk\\platform-tools
   - Add: C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk\\cmdline-tools\\latest\\bin

4. Set Environment Variables:
   - ANDROID_SDK_ROOT=C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk
   - ANDROID_HOME=C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk

5. Accept Licenses:
   - Run: sdkmanager --licenses

6. Install SDK Components:
   - Run: sdkmanager "platforms;android-34"
   - Run: sdkmanager "system-images;android-34;google_apis;x86_64"
   - Run: sdkmanager "emulator"

Alternatively, use Android Studio for a graphical setup:
   https://developer.android.com/studio
"""

    def _get_macos_instructions(self) -> str:
        return """
Android SDK Setup Instructions (macOS)
=======================================

1. Install via Homebrew (recommended):
   brew install android-sdk

2. Or download manually:
   - Visit: https://developer.android.com/studio/command-line-tools
   - Download the macOS version

3. Set Environment Variables (add to ~/.zshrc or ~/.bash_profile):
   export ANDROID_SDK_ROOT=$HOME/Library/Android/sdk
   export ANDROID_HOME=$ANDROID_SDK_ROOT
   export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
   export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools

4. Accept Licenses:
   sdkmanager --licenses

5. Install SDK Components:
   sdkmanager "platforms;android-34"
   sdkmanager "system-images;android-34;google_apis;x86_64"
   sdkmanager "emulator"

Alternatively, use Android Studio:
   https://developer.android.com/studio
"""

    def _get_linux_instructions(self) -> str:
        return """
Android SDK Setup Instructions (Linux)
=======================================

1. Install via package manager (Ubuntu/Debian):
   sudo apt-get update
   sudo apt-get install android-sdk

2. Or download manually:
   - Visit: https://developer.android.com/studio/command-line-tools
   - Download the Linux version

3. Set Environment Variables (add to ~/.bashrc or ~/.zshrc):
   export ANDROID_SDK_ROOT=$HOME/Android/Sdk
   export ANDROID_HOME=$ANDROID_SDK_ROOT
   export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
   export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools

4. Accept Licenses:
   sdkmanager --licenses

5. Install SDK Components:
   sdkmanager "platforms;android-34"
   sdkmanager "system-images;android-34;google_apis;x86_64"
   sdkmanager "emulator"

Note: On Linux, you may also need to install KVM for hardware acceleration:
   sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients

Alternatively, use Android Studio:
   https://developer.android.com/studio
"""

    def update_config_yaml(self, config_path: Path = None):
        """Update config.yaml with detected SDK paths"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config.yaml"

        if not self.sdk_root or not self.adb_path:
            print("Cannot update config: SDK components not found")
            return False

        try:
            import yaml
        except ImportError:
            print("PyYAML not installed, cannot update config.yaml")
            return False

        # Read existing config
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        # Update Android SDK paths
        if "android_sdk" not in config:
            config["android_sdk"] = {}

        config["android_sdk"]["root"] = str(self.sdk_root)
        config["android_sdk"]["adb"] = str(self.adb_path)
        if self.emulator_path:
            config["android_sdk"]["emulator"] = str(self.emulator_path)
        if self.avdmanager_path:
            config["android_sdk"]["avdmanager"] = str(self.avdmanager_path)

        # Write config back
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        print(f"✓ Updated configuration in {config_path}")
        return True


def main():
    """Main entry point for testing"""
    manager = AndroidSDKManager()
    status = manager.print_status()

    if not status["sdk_found"]:
        print("\n❌ Android SDK not found!")
        print(manager.get_sdk_setup_instructions())
        return 1

    if not all(status.get(key, False) for key in ["adb", "emulator", "avdmanager"]):
        print("\n⚠️  Some SDK components are missing")
        return 0

    print("✓ All required Android SDK components found!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
