@echo off
echo Starting DevOps Agent...
echo.

echo Starting Backend Server...
start cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dashboard...
start cmd /k "cd frontend && npm start"

echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul
