#!/bin/bash
# Android Multi-Emulator Manager Launcher for macOS

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found!"
    echo "Please run ./setup_macos.sh first to set up the application."
    exit 1
fi

# Run the application
python main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Failed to start the application."
    echo ""
    echo "If you haven't set up the application yet, run ./setup_macos.sh first."
    echo "Or ensure Python is installed and dependencies are installed:"
    echo "  pip install -r requirements.txt"
    exit 1
fi
