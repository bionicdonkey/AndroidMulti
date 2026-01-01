# Android Multi-Emulator Manager

A production-ready Windows application for managing multiple Android emulator instances with synchronized input capabilities. Create, manage, and control multiple cloned emulators simultaneously with an intuitive graphical interface.

## Features

- 🚀 **Multiple Emulator Management**: Create and manage multiple Android emulator instances simultaneously
- 📱 **AVD Cloning**: Easily clone existing AVD templates to run multiple instances
- 🔄 **Input Synchronization**: Sync touch, keyboard, and scroll input across multiple emulators
- 🎮 **Independent Operation**: Each emulator can also operate independently when sync is disabled
- ⚡ **Hardware Acceleration**: Automatic detection and configuration of hardware acceleration (HAXM, WHPX)
- 🎨 **Modern UI**: Intuitive PyQt6-based interface with dark theme support
- 🔧 **Windows Optimized**: Built specifically for Windows with native optimizations

## Requirements

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: Minimum 8GB (16GB+ recommended for multiple emulators)
- **Storage**: At least 10GB free space per emulator instance

### Software Requirements
- **Python 3.8+**
- **Android SDK** with:
  - Android Emulator
  - ADB (Android Debug Bridge)
  - AVD Manager
  - Platform Tools

### Hardware Acceleration (Recommended)
- **Intel HAXM** or **Windows Hypervisor Platform (WHPX)** for optimal performance

## Installation

### Quick Start (Automated Setup)

The easiest way to set up the application is to use the platform-specific setup scripts, which automatically create a virtual environment, install dependencies, and check for Android SDK:

**Windows:**
```cmd
setup.bat
```

**Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**macOS:**
```bash
chmod +x setup_macos.sh
./setup_macos.sh
```

### Manual Setup

If you prefer manual setup or the scripts don't work for your system:

#### 1. Create a Virtual Environment

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Note:** If you encounter execution policy errors in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Python Dependencies

With your virtual environment activated, install the dependencies:

```bash
pip install -r requirements.txt
```

#### 3. Configure Android SDK

The application will automatically detect your Android SDK installation. You can verify the installation status by running:

```bash
python src/android_sdk_setup.py
```

This script will:
- Check for Android SDK in common installation locations
- Verify the presence of required tools (ADB, Emulator, AVD Manager)
- Display setup instructions if components are missing

If auto-detection fails, manually set environment variables:
- `ANDROID_SDK_ROOT` (preferred)
- `ANDROID_HOME` (legacy)

Or manually configure paths in `config.yaml`:

**Windows:**
```yaml
android_sdk:
  root: "C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk"
  emulator: "C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk\\emulator\\emulator.exe"
  adb: "C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"
  avd_manager: "C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk\\cmdline-tools\\latest\\bin\\avdmanager.bat"
```

**Linux/macOS:**
```yaml
android_sdk:
  root: "/home/username/Android/Sdk"  # or ~/Library/Android/sdk on macOS
  emulator: "/home/username/Android/Sdk/emulator/emulator"
  adb: "/home/username/Android/Sdk/platform-tools/adb"
  avd_manager: "/home/username/Android/Sdk/cmdline-tools/latest/bin/avdmanager"
```

### Android SDK Installation

If you don't have Android SDK installed, the setup script will provide platform-specific instructions. Here's a quick summary:

#### Windows
1. Download Android SDK Command-line Tools from: https://developer.android.com/studio/command-line-tools
2. Extract to: `C:\Users\YourUsername\AppData\Local\Android\Sdk`
3. Set environment variable: `ANDROID_SDK_ROOT=C:\Users\YourUsername\AppData\Local\Android\Sdk`
4. Install components:
   ```cmd
   sdkmanager "platforms;android-34"
   sdkmanager "system-images;android-34;google_apis;x86_64"
   sdkmanager "emulator"
   sdkmanager --licenses
   ```

#### Linux
1. Install via package manager (Ubuntu/Debian):
   ```bash
   sudo apt-get update
   sudo apt-get install android-sdk
   ```
   Or download manually from: https://developer.android.com/studio/command-line-tools
2. Set environment variables in `~/.bashrc` or `~/.zshrc`:
   ```bash
   export ANDROID_SDK_ROOT=$HOME/Android/Sdk
   export ANDROID_HOME=$ANDROID_SDK_ROOT
   export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
   export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools
   ```
3. Install components:
   ```bash
   sdkmanager "platforms;android-34"
   sdkmanager "system-images;android-34;google_apis;x86_64"
   sdkmanager "emulator"
   sdkmanager --licenses
   ```
4. (Optional) Enable KVM for hardware acceleration:
   ```bash
   sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients
   sudo usermod -a -G kvm $USER
   ```

#### macOS
1. Install via Homebrew (recommended):
   ```bash
   brew install android-sdk
   ```
   Or download manually from: https://developer.android.com/studio/command-line-tools
2. Set environment variables in `~/.zshrc` or `~/.bash_profile`:
   ```bash
   export ANDROID_SDK_ROOT=$HOME/Library/Android/sdk
   export ANDROID_HOME=$ANDROID_SDK_ROOT
   export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
   export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools
   ```
3. Install components:
   ```bash
   sdkmanager "platforms;android-34"
   sdkmanager "system-images;android-34;google_apis;x86_64"
   sdkmanager "emulator"
   sdkmanager --licenses
   ```

### 4. Create AVD Templates

Before using the application, you need to create at least one AVD (Android Virtual Device) template using Android Studio's AVD Manager or command line:

**Using Android Studio:**
1. Open Android Studio
2. Go to Tools → Device Manager (or Tools → AVD Manager on older versions)
3. Create Virtual Device
4. Select a device definition and system image
5. Finish the setup

**Using Command Line:**
```bash
avdmanager create avd -n MyAVD -k "system-images;android-34;google_apis;x86_64"
```

## Running the Application

### Automated Launch

Use the platform-specific run scripts:

**Windows:**
```cmd
run.bat
```

**Linux:**
```bash
./run.sh
```

**macOS:**
```bash
./run_macos.sh
```

### Manual Launch

With virtual environment activated:
```bash
python main.py
```

## Usage

### Creating Emulator Instances

1. Click **"➕ Create Emulator"** button
2. Select an AVD template from the dropdown
3. (Optional) Enter a custom instance name
4. Check **"Create as clone"** to allow multiple instances (recommended)
5. Click **"Create & Start"**

The emulator will start in the background. You can monitor its status in the "Running Emulators" table.

### Managing Emulators

- **Stop**: Select an emulator and click **"🛑 Stop"**
- **Restart**: Select an emulator and click **"🔄 Restart"**
- **View Status**: Monitor state (Starting/Running/Stopped) in the table

### Input Synchronization

#### Enable Global Sync
1. Check **"Enable Sync"** checkbox in the toolbar
2. All running emulators will be added to the sync group

#### Individual Instance Sync
- Use the checkbox in the "Sync" column for each emulator to include/exclude it from synchronization

#### Sync Settings
- **Delay (ms)**: Add a delay between sending input to each emulator (useful for testing timing)

#### Synchronized Input Types
- ✅ Touch/Tap events
- ✅ Keyboard input
- ✅ Scroll gestures

When sync is enabled, input from any synchronized emulator will be replicated to all others. When disabled, each emulator operates independently.

## Configuration

Edit `config.yaml` to customize application settings:

```yaml
# Emulator defaults
emulator:
  hardware_acceleration: true  # Enable hardware acceleration
  default_ram: 2048  # MB
  default_vm_heap: 256  # MB
  default_screen_density: 420  # DPI
  default_screen_resolution: "1080x1920"

# Input synchronization
input_sync:
  enabled: false  # Start with sync disabled
  sync_touch: true
  sync_keyboard: true
  sync_scroll: true
  delay_ms: 0  # Delay between emulators

# UI settings
ui:
  theme: "dark"  # "dark" or "light"
  auto_refresh_interval: 2  # seconds
  show_emulator_preview: true
```

## Architecture

### Project Structure

```
AndroidMulti/
├── main.py                 # Application entry point
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── src/
    ├── __init__.py
    ├── config_manager.py      # Configuration management
    ├── emulator_manager.py    # Emulator lifecycle management
    ├── input_synchronizer.py  # Input synchronization logic
    └── gui/
        ├── __init__.py
        └── main_window.py     # Main GUI application
```

### Key Components

- **ConfigManager**: Handles configuration loading/saving and Android SDK path detection
- **EmulatorManager**: Manages emulator instances, AVD cloning, start/stop operations
- **InputSynchronizer**: Handles input replication across synchronized emulators
- **MainWindow**: PyQt6-based GUI for user interaction

## Hardware Acceleration

The application automatically detects and configures the best available acceleration method:

1. **Windows Hypervisor Platform (WHPX)** - Recommended for Windows 10/11
2. **Intel HAXM** - Legacy support for older systems
3. **Auto** - Let the emulator choose the best option

Hardware acceleration significantly improves emulator performance, especially when running multiple instances.

## Troubleshooting

### Emulator won't start
- Verify Android SDK paths in `config.yaml`
- Check that AVD template exists and is valid
- Ensure hardware acceleration is properly configured
- Check Windows Defender/exceptions if virtualization is blocked

### Input sync not working
- Verify ADB connection: `adb devices`
- Ensure emulators are in "Running" state
- Check that sync is enabled for target instances
- Verify ADB path is correct in configuration

### Performance issues
- Enable hardware acceleration
- Reduce number of running emulators
- Increase available RAM allocation
- Close unnecessary applications

### AVD cloning fails
- Ensure source AVD exists and is not currently running
- Check disk space availability
- Verify write permissions in `.android/avd` directory

## Limitations

- Requires existing AVD templates (cannot create new ones through the UI)
- Input synchronization uses ADB commands (some limitations with complex gestures)
- Maximum concurrent instances limited by system resources
- GUI currently optimized for Windows/Linux (macOS support included but less tested)

## Development

### Running from Source

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Code Structure

The application follows a modular architecture:
- Business logic separated from UI
- Configuration-driven design
- Error handling and logging ready for production use

## License

This project is provided as-is for managing Android emulator instances.

## Support

For issues, questions, or contributions, please refer to the project repository.

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- New features include appropriate error handling
- UI changes maintain accessibility and usability
- Documentation is updated for significant changes
