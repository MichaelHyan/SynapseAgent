@echo off
cd /d "%~dp0"
pip install -r requirements.txt -q 2>nul
start "SynapseAgent Web" python ./web/server.py
timeout /t 2 /nobreak >nul
start http://localhost:5001
