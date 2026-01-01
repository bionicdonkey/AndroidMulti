@echo off
REM Android Multi-Emulator Manager Launcher for Windows

REM Check if virtual environment exists and activate it
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the application
python main.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo.
    echo If you haven't set up the virtual environment yet, run setup.bat first.
    echo Or ensure Python is installed and dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
