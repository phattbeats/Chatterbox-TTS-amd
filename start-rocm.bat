@echo off
cd /d %~dp0
echo.
echo ============================================================
echo    PHATT TECH Chatterbox TTS Server - ROCm Launcher
echo ============================================================
echo.
python start.py --rocm-windows
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check the output above.
    echo.
    echo If the issue is with wheel installation, download the
    echo wheels manually from the GitHub releases page and place
    echo them in a 'wheels' folder next to this script.
    echo.
)
pause
