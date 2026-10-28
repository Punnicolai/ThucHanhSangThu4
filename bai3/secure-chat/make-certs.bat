@echo off
cd /d "%~dp0"
python make_certs.py --out certs
if errorlevel 1 exit /b 1
echo Certificate keys are local only. Do not commit certs/.
