@echo off
REM Setup script for Android Multi-Emulator Manager
REM Creates virtual environment, installs dependencies, and checks Android SDK

setlocal enabledelayedexpansion

echo ========================================
echo Android Multi-Emulator Manager Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

echo.
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [3/3] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Checking Android SDK installation...
python src\android_sdk_setup.py

if errorlevel 1 (
    echo.
    echo WARNING: Android SDK not found or incomplete
    echo.
    echo The application requires Android SDK with:
    echo   - Android Emulator
    echo   - ADB (Android Debug Bridge)
    echo   - AVD Manager
    echo.
    echo Would you like to see setup instructions? (Requires manual setup)
    echo.
    set /p install_choice="Install Android SDK now? (y/n): "
    if /i "!install_choice!"=="y" (
        REM Open setup instructions URL or display them
        echo.
        echo Showing Android SDK setup instructions...
        python -c "from src.android_sdk_setup import AndroidSDKManager; m = AndroidSDKManager(); print(m.get_sdk_setup_instructions())"
        pause
    )
    exit /b 1
)

echo.
echo ========================================
echo Setup completed successfully!
echo All components verified!
echo ========================================
echo.
echo To run the application:
echo   1. Activate the virtual environment: venv\Scripts\activate.bat
echo   2. Run: python main.py
echo.
echo Or simply double-click run.bat
echo.
pause
exit /b 0
