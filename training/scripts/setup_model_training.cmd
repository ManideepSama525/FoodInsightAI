@echo off
setlocal EnableExtensions

cd /d "%~dp0\..\.."

echo ============================================================
echo FoodInsightAI - Model Training Environment
echo ============================================================

if not exist ".venv" (
    echo Creating Python 3.12 virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

python --version
python -c "import sys; assert sys.version_info[:2] == (3,12), 'FoodInsightAI training expects Python 3.12.'"
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -r training\requirements-model-training.txt
if errorlevel 1 goto :error

python training\scripts\verify_training_environment.py
if errorlevel 1 goto :error

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo Next:
echo   training\scripts\download_baseline.cmd
echo   training\scripts\prepare_dataset.cmd
echo   training\scripts\train.cmd
echo   training\scripts\evaluate.cmd
exit /b 0

:error
echo.
echo SETUP FAILED.
exit /b 1
