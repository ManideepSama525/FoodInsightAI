@echo off
setlocal
if not exist models mkdir models
echo Downloading Qwen3-1.7B-Base...
hf download Qwen/Qwen3-1.7B-Base --local-dir models\Qwen3-1.7B-Base
if errorlevel 1 exit /b 1
echo QWEN3 DOWNLOAD: OK
