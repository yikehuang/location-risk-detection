@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is not available in PATH. Install Python 3, then retry.
  pause
  exit /b 1
)

set "ADB=C:\Program Files (x86)\Nemu\vmonitor\bin\adb_server.exe"
set "SERIAL=127.0.0.1:7555"
if not exist "%ADB%" (
  echo MuMu built-in ADB was not found at:
  echo %ADB%
  echo Edit the ADB path in run_mumu_demo.bat to match your MuMu installation.
  pause
  exit /b 1
)

start "Location Risk Lab API" /D "%~dp0" cmd /k python server.py
timeout /t 3 /nobreak >nul

"%ADB%" connect %SERIAL%
if errorlevel 1 (
  echo Could not connect to MuMu. Check that MuMu Player is running and update SERIAL if its ADB port differs.
  pause
  exit /b 1
)

"%ADB%" -s %SERIAL% reverse tcp:8000 tcp:8000
if errorlevel 1 (
  echo ADB port forwarding failed. Check the MuMu ADB connection and retry.
  pause
  exit /b 1
)

"%ADB%" -s %SERIAL% shell am start -a android.intent.action.VIEW -d http://127.0.0.1:8000/
if errorlevel 1 (
  echo Could not open the demo page in MuMu. Open the browser and visit http://127.0.0.1:8000/
  pause
  exit /b 1
)

echo Location Risk Lab is open in MuMu. Leave the API command window running during the demo.
pause
