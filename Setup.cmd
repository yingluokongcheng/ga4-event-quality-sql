@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3.12 scripts\setup_local.py
) else (
  python scripts\setup_local.py
)
if errorlevel 1 (
  echo Setup failed. Read the error above. No cloud account is required.
) else (
  echo Setup complete. Open Start_dashboard.cmd.
)
pause
