@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1
python training\scripts\train_foodinsight_lora.py
exit /b %errorlevel%
