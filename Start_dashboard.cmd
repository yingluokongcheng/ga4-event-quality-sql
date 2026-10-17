@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup.cmd first.
  pause
  exit /b 1
)
if not exist "data\warehouse\audit.duckdb" (
  echo Data has not been prepared. Run Setup.cmd first.
  pause
  exit /b 1
)
echo Opening http://127.0.0.1:8501 . Keep this window open; Ctrl+C stops the dashboard.
.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.headless=false --browser.gatherUsageStats=false
if errorlevel 1 pause
