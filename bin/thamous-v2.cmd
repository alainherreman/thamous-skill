@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%..\scripts\thamous_api_v2.py" %*
