@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo FoodInsightAI - complete local setup
echo ================================================
echo.

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example
)

echo [1/3] Installing backend...
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e backend

echo.
echo [2/3] Installing local model/training stack...
python -m pip install -r backend\requirements-local-model.txt
python -m pip install -r training\requirements-model-training.txt

echo.
echo [3/3] Installing frontend...
cd frontend
call npm install
cd ..

echo.
echo ================================================
echo Setup complete.
echo No API credentials are required for the default
echo local/mock development configuration.
echo ================================================
echo.
echo To build containers:
echo   docker compose build
echo.
echo To start the application:
echo   docker compose up
echo.
echo To download and prepare the USDA training data:
echo   training\scripts\download_and_prepare_usda.cmd
echo.
echo To train:
echo   training\scripts\train.cmd
echo.
