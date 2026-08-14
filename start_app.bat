@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo.
    echo Please follow the setup instructions in README.md first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" run.py
if errorlevel 1 (
    echo.
    echo The application stopped with an error.
    pause
)
