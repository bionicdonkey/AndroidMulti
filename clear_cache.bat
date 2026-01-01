@echo off
REM Clear Python cache files
echo Clearing Python cache files...

for /r . %%d in (__pycache__) do @if exist "%%d" (
    echo Removing %%d
    rd /s /q "%%d" 2>nul
)

for /r . %%f in (*.pyc) do @if exist "%%f" (
    echo Removing %%f
    del /q "%%f" 2>nul
)

echo Cache cleared!
pause
