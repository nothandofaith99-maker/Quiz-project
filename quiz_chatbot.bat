@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw -3 "%~dp0quiz_app.py"
    exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw "%~dp0quiz_app.py"
    exit /b 0
)

echo Could not find Python 3. Install Python and make sure it is on PATH.
pause
