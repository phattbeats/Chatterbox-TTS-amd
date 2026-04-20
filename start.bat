@echo off
cd /d %~dp0
echo.
echo ============================================================
echo    PHATT TECH Chatterbox TTS Server - Launcher
echo ============================================================
echo.
python start.py --rocm-windows
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check the output above.
    echo.
    echo If installation failed, make sure you are on Windows 11 with
    echo AMD Radeon RX 6000 series GPU and ROCm drivers installed.
    echo See PHATT_FORK.md for requirements.
    echo.
)
pause