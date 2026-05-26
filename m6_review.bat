@echo off
chcp 65001 > nul
cd /d "%~dp0"
D:\Users\yando\miniconda3\envs\cooling_rag_env\pythonw.exe scripts\m6_review_ui.py
if %errorlevel% neq 0 (
    D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe scripts\m6_review_ui.py
    echo.
    echo Startup failed - see error above
    pause
)
