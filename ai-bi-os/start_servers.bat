@echo off
cd /d "%~dp0"
echo ===================================================
echo Starting AI BI OS (Enterprise AI Decision Platform)
echo ===================================================

echo.
echo Cleaning up existing processes...
call npx -y kill-port 3000 8000

echo Waiting for ports to be released...
ping 127.0.0.1 -n 4 > nul

echo.
echo Cleaning Next.js cache...
if exist "frontend\.next" rd /s /q "frontend\.next"
if exist "frontend\node_modules\.cache" rd /s /q "frontend\node_modules\.cache"

echo.
echo [1/2] Starting Python FastAPI Backend...
cd backend
start cmd /k ".\venv\Scripts\activate && python -m uvicorn app.main:app --reload --reload-dir app --port 8000"
cd ..

echo [2/2] Starting Next.js Frontend...
cd frontend
start cmd /k "npm run dev"
cd ..

echo.
echo All services are starting up!
echo The dashboard will be available at http://localhost:3000
echo The API will be available at http://127.0.0.1:8000
echo ===================================================
pause
