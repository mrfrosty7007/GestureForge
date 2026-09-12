@echo off
title GestureForge Launcher
cd /d "%~dp0"
echo ===================================================
echo   Starting GestureForge Native Camera App...
echo ===================================================
echo.
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe main.py %*
) else (
    uv run python main.py %*
)
if errorlevel 1 (
    echo.
    echo Application exited with code %errorlevel%.
    pause
)
