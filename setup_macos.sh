#!/bin/bash
# Setup script for Android Multi-Emulator Manager on macOS
# Creates virtual environment and installs dependencies, checks Android SDK

set -e  # Exit on error

echo "========================================"
echo "Android Multi-Emulator Manager Setup"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ using Homebrew:"
    echo "  brew install python@3.11"
    echo ""
    echo "Or download from: https://www.python.org/downloads/macos/"
    exit 1
fi

python3_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python3_version"
echo ""

# Step 1: Create virtual environment
echo "[1/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created successfully!"
fi

echo ""

# Step 2: Activate virtual environment
echo "[2/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "✓ Virtual environment activated"

echo ""

# Step 3: Install dependencies
echo "[3/4] Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed successfully!"

echo ""

# Step 4: Check Android SDK
echo "[4/4] Checking Android SDK installation..."
python src/android_sdk_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: Android SDK not found or incomplete"
    echo ""
    echo "The application requires Android SDK with:"
    echo "  - Android Emulator"
    echo "  - ADB (Android Debug Bridge)"
    echo "  - AVD Manager"
    echo ""
    read -p "Would you like to see Android SDK setup instructions? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python -c "from src.android_sdk_setup import AndroidSDKManager; m = AndroidSDKManager(); print(m.get_sdk_setup_instructions())"
    fi
    exit 1
fi

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "All components verified!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo ""
echo "Or simply run: ./run.sh"
echo ""
