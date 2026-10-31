@echo off
setlocal
cd /d "%~dp0"
if not exist "outputs\run_status.json" (
    echo You must run run_all.bat successfully first.
    pause
    exit /b 1
)
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
%PY% -m scripts.build_portfolio_showcase
if errorlevel 1 goto failed
%PY% -m scripts.build_powerbi_project
if errorlevel 1 goto failed
%PY% -m scripts.build_case_study
if errorlevel 1 goto failed
%PY% -m scripts.build_showcase_preview
if errorlevel 1 goto failed
echo.
echo SUCCESS. Portfolio assets have been rebuilt.
echo Open dashboards\interactive_dashboard.html, case-study.html, and powerbi\
pause
exit /b 0
:failed
echo.
echo SHOWCASE BUILD FAILED. Check that run_all.bat succeeded and dependencies are installed.
pause
exit /b 1
