@echo off
cd /d "%~dp0"
echo ===================================================
echo Starting AI BI OS (Enterprise AI Decision Platform)
echo ===================================================

echo.
echo [1/2] Starting Python FastAPI Backend...
cd backend
start cmd /k "python -m pip install -r requirements.txt && python -m uvicorn app.main:app --reload --port 8000"

cd ..

echo [2/2] Starting Next.js Frontend...
cd frontend
start cmd /k "npm install && npm run dev"

echo.
echo All services are starting up!
echo The dashboard will be available at http://localhost:3000
echo The API will be available at http://localhost:8000
echo ===================================================
pause
