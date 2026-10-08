@echo off
setlocal
cd /d "%~dp0..\.."
echo.
echo ================================================
echo FoodInsightAI - USDA download + dataset build
echo ================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Creating project Python environment...
  py -3.12 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r training\requirements-model-training.txt
python training\scripts\download_and_prepare_usda.py
if errorlevel 1 (
  echo.
  echo USDA preparation failed.
  exit /b 1
)
echo.
echo USDA dataset and leakage-controlled task splits are ready.
exit /b 0
