@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1
python training\scripts\prepare_training_dataset.py
exit /b %errorlevel%
