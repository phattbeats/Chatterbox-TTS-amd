@echo off
cd /d %~dp0
echo.
echo ============================================================
echo    PHATT TECH Chatterbox TTS Server - ROCm Launcher
echo ============================================================
echo.
python start-rocm.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check the output above.
    echo.
)
pause