@echo off
cd /d %~dp0
cd frontend
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)
echo Starting Frontend Server...
call npm run dev
pause
