@echo off
echo Setting up DevOps Agent...
echo.

echo Installing Backend Dependencies...
cd backend
python -m pip install -r requirements.txt
cd ..

echo.
echo Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo Setup complete!
echo Run start.bat to start the application.
