@echo off
cd /d "%~dp0"
echo ===================================================
echo AI BI OS - Environment Setup
echo ===================================================
echo.
echo Installing Backend Dependencies...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call .\venv\Scripts\activate
python -m pip install -r requirements.txt
cd ..

echo.
echo Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo Setup Complete! You can now run start_servers.bat
echo ===================================================
pause
