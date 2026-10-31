@echo off
setlocal
cd /d "%~dp0"
echo Bangladesh Food Price and Inflation Risk Analysis
if exist ".venv\Scripts\python.exe" goto install
py -3 --version >nul 2>&1
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto fail
goto install
:usepython
python --version >nul 2>&1
if errorlevel 1 goto nopython
python -m venv .venv
if errorlevel 1 goto fail
:install
.venv\Scripts\python.exe -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10 or newer required'"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist .env copy .env.example .env >nul
.venv\Scripts\python.exe run_all.py
if errorlevel 1 goto fail
echo Finished. Open docs\FINDINGS.md and outputs.
pause
exit /b 0
:nopython
echo Python was not found. Install Python 3.10+ and select Add Python to PATH.
:fail
echo Run stopped. Read the message above and outputs\pipeline.log if present.
pause
exit /b 1
