@echo off
echo ============================================================
echo   Smart Attendance Application
echo ============================================================
echo.
echo Starting backend server...
cd backend
start cmd /c "python app.py"
echo Waiting for server to start...
ping 127.0.0.1 -n 7 > nul
echo Opening browser...
start http://localhost:8000
echo.
echo Application opened! Check your browser.
echo.
pause
