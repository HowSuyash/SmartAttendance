@echo off
echo Smart Attendance Application
echo.
cd backend
start "" python app.py
timeout /t 5 >nul 2>&1
start http://localhost:8000
echo Application running at http://localhost:8000
echo Close the Python window to stop the server
