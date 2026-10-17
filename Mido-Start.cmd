@echo off
rem ==========================================================================
rem  Mido - start the userbot on Windows (double-click this file)
rem  - uses the project .venv when present
rem  - keeps the window open so you can read any error
rem  For automatic start at logon see deploy\WINDOWS-RDP.md (Task Scheduler).
rem  (This file is intentionally ASCII-only: cmd.exe reads batch files in the
rem   OEM code page, so Arabic text here would be garbled.)
rem ==========================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"

if exist ".venv\Scripts\python.exe" (
    set "MIDO_PY=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo.
        echo   [x] Python was not found.
        echo       Run first:  powershell -ExecutionPolicy Bypass -File .\Mido-RDP-Install.ps1
        echo.
        pause
        exit /b 2
    )
    set "MIDO_PY=python"
)

echo.
echo   Mido - starting...  (press Ctrl+C to stop)
echo.
"%MIDO_PY%" -m zira
set "MIDO_EXIT=%errorlevel%"

echo.
if not "%MIDO_EXIT%"=="0" (
    echo   [x] Mido stopped with exit code %MIDO_EXIT%
    echo       Check the messages above, or run:  "%MIDO_PY%" mido_setup.py check
) else (
    echo   [i] Mido stopped.
)
echo.
pause
exit /b %MIDO_EXIT%
