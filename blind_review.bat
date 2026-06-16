@echo off
chcp 65001 > nul
cd /d "%~dp0"
D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe -m streamlit run scripts\blind_correctness_review_ui.py --server.port 8508
if %errorlevel% neq 0 (
    echo.
    echo Startup failed - see error above
    pause
)
