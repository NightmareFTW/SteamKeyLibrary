@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "steamkeylibrary.py"
) else (
    start "" pythonw "steamkeylibrary.py"
)
