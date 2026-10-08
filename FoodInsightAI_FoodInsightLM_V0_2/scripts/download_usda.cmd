@echo off
setlocal
python scripts\download_usda_v02.py
if errorlevel 1 exit /b 1
echo USDA ACQUISITION: OK
