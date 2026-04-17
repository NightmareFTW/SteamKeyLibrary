@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo Using Python: %PY%
"%PY%" -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

"%PY%" -m PyInstaller --noconfirm --clean --windowed --onefile --name "SteamKeyLibrary" "steamkeylibrary.py"
if errorlevel 1 goto :error

echo.
echo Build complete.
echo EXE location: dist\SteamKeyLibrary.exe
goto :end

:error
echo.
echo Build failed.
exit /b 1

:end
endlocal
