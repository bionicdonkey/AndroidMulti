# Quick Start Guide

## Automated Setup (Recommended)

The easiest way to get started is to use the automated setup script for your platform:

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

These scripts will:
1. ✓ Create a Python virtual environment
2. ✓ Install all dependencies
3. ✓ Check for Android SDK and guide you through setup if needed

## Manual Setup

If the automated setup doesn't work for you, follow these steps:

### 1. Install Python 3.8+

Download from [python.org](https://www.python.org/downloads/)

### 2. Create Virtual Environment

**Windows (Command Prompt):**
## Running the Application

### Automated Launch (Recommended)

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

## Android SDK Setup

If the setup script indicates Android SDK is missing, you have two options:

### Option 1: Automatic Setup (Easiest)
Run the setup script again and choose the option to see installation instructions for your platform.

### Option 2: Manual Setup

**Windows:**
1. Download Android SDK Command-line Tools
2. Set environment variable: `ANDROID_SDK_ROOT=C:\Users\YourUsername\AppData\Local\Android\Sdk`
3. Accept licenses: `sdkmanager --licenses`

**Linux/macOS:**
1. Install via Homebrew (macOS) or package manager (Linux)
2. Set environment variable: `export ANDROID_SDK_ROOT=$HOME/Android/Sdk` (or `~/Library/Android/sdk` on macOS)
3. Accept licenses: `sdkmanager --licenses`

See the main [README.md](README.md) for detailed platform-specific instructions.

## Create Android Virtual Devices (AVDs)

Before using the app, create at least one AVD template:

**Using Android Studio:**
1. Open Android Studio
2. Go to Tools → Device Manager
3. Create a new Virtual Device

**Using Command Line:**
```bash
avdmanager create avd -n MyAVD -k "system-images;android-34;google_apis;x86_64"
```

## First Use

1. Launch the application
2. Click **"➕ Create Emulator"**
3. Select an AVD template from the dropdown
4. Check **"Create as clone"** to create multiple instances
5. Click **"Create & Start"**
6. Manage emulators using the interface
5. Click **"Create & Start"**
6. Wait for emulator to boot (may take 1-2 minutes)

## Basic Operations

### Create Multiple Emulators
- Repeat the creation process to start multiple instances
- Each instance runs independently on a separate port

### Enable Input Sync
- Check **"Enable Sync"** in the toolbar to sync all running emulators
- Or use individual checkboxes in the "Sync" column for selective sync
- Input (touch, keyboard) will be replicated to all synced emulators

### Stop Emulators
- Select an emulator in the table
- Click **"🛑 Stop"** button
- Or close the emulator window directly

## Tips

- **Performance**: Enable hardware acceleration for best performance
- **Resources**: Each emulator uses ~2GB RAM by default
- **Ports**: Emulators use ports 5554, 5556, 5558, etc. (even numbers)
- **AVD Clones**: Cloned AVDs are stored in `~/.android/avd/`

## Troubleshooting

**Emulator won't start?**
- Check Android SDK paths in `config.yaml`
- Verify AVD template exists
- Ensure hardware acceleration is available (HAXM/WHPX)

**Sync not working?**
- Ensure emulators show "Running" state
- Verify ADB connection: `adb devices`
- Check sync checkboxes are enabled

**Need help?** See the full [README.md](README.md) for detailed documentation.
