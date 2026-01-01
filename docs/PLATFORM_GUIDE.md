# Platform-Specific Quick Commands

A quick reference for setup and running the Android Multi-Emulator Manager on different platforms.

## Windows

### First Time Setup
```cmd
setup.bat
```

### Running the Application
```cmd
run.bat
```

### Manual Setup
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python src\android_sdk_setup.py
```

### Manual Run
```cmd
venv\Scripts\activate.bat
python main.py
```

### Check Android SDK
```cmd
python src\android_sdk_setup.py
```

---

## Linux

### First Time Setup
```bash
chmod +x setup.sh
./setup.sh
```

### Running the Application
```bash
./run.sh
```

### Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/android_sdk_setup.py
```

### Manual Run
```bash
source venv/bin/activate
python main.py
```

### Check Android SDK
```bash
python src/android_sdk_setup.py
```

### Install Android SDK (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install android-sdk
```

### Optional: Enable Hardware Acceleration (KVM)
```bash
sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients
sudo usermod -a -G kvm $USER
```

---

## macOS

### First Time Setup
```bash
chmod +x setup_macos.sh
./setup_macos.sh
```

### Running the Application
```bash
./run_macos.sh
```

### Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/android_sdk_setup.py
```

### Manual Run
```bash
source venv/bin/activate
python main.py
```

### Check Android SDK
```bash
python src/android_sdk_setup.py
```

### Install Android SDK via Homebrew
```bash
brew install android-sdk
```

### Install Python via Homebrew
```bash
brew install python@3.11
```

---

## Common Tasks (All Platforms)

### Create AVD Template
```bash
avdmanager create avd -n MyAVD -k "system-images;android-34;google_apis;x86_64"
```

### List AVD Templates
```bash
avdmanager list avd
```

### Check ADB Devices
```bash
adb devices
```

### Accept Android Licenses
```bash
sdkmanager --licenses
```

### Verify Python Installation
```bash
python --version      # Windows
python3 --version     # Linux/macOS
```

---

## Troubleshooting Quick Fixes

### "Virtual environment not found" Error
**Solution:** Run setup script first
```bash
./setup.sh      # Linux/macOS
setup.bat       # Windows
```

### "Python not installed" Error
**Windows:** Download from https://www.python.org/downloads/
**Linux:** `sudo apt-get install python3 python3-venv`
**macOS:** `brew install python@3.11`

### "Android SDK not found" Error
**Solution:** Run the setup script - it will show installation instructions
```bash
python src/android_sdk_setup.py
```

### "Permission denied" on run.sh or setup.sh
**Solution:** Make scripts executable
```bash
chmod +x setup.sh run.sh setup_macos.sh run_macos.sh
```

### "ModuleNotFoundError" for dependencies
**Solution:** Reinstall dependencies in virtual environment
```bash
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

---

## Environment Variables

Set these to customize Android SDK location:

### Windows (Command Prompt - Admin)
```cmd
setx ANDROID_SDK_ROOT "C:\Users\YourUsername\AppData\Local\Android\Sdk"
setx ANDROID_HOME "C:\Users\YourUsername\AppData\Local\Android\Sdk"
```

### Linux (Add to ~/.bashrc)
```bash
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_HOME=$ANDROID_SDK_ROOT
```

### macOS (Add to ~/.zshrc)
```bash
export ANDROID_SDK_ROOT=$HOME/Library/Android/sdk
export ANDROID_HOME=$ANDROID_SDK_ROOT
```

Then reload: `source ~/.bashrc` or `source ~/.zshrc`

---

## File Reference

| File | Purpose | Platform |
|------|---------|----------|
| `setup.bat` | Initial setup | Windows |
| `run.bat` | Launch application | Windows |
| `setup.sh` | Initial setup | Linux |
| `run.sh` | Launch application | Linux |
| `setup_macos.sh` | Initial setup | macOS |
| `run_macos.sh` | Launch application | macOS |
| `src/android_sdk_setup.py` | SDK detection utility | All |
| `config.yaml` | Application configuration | All |
| `requirements.txt` | Python dependencies | All |

---

## Performance Tips

### Windows
- Use Windows Hypervisor Platform (WHPX) for hardware acceleration
- Ensure VT-x/AMD-V is enabled in BIOS

### Linux
- Enable KVM for hardware acceleration
- Run: `kvm-ok` to check if KVM is available

### macOS
- Ensure Hypervisor framework is available
- Use Apple Silicon (ARM64) for better performance if available

---

## Getting Help

1. **Check Documentation:** See README.md for detailed information
2. **Quick Start:** See QUICKSTART.md for step-by-step instructions
3. **Setup Details:** See SETUP_OVERVIEW.md for architecture details
4. **Run SDK Checker:** `python src/android_sdk_setup.py` for diagnostics
