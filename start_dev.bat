@echo off
REM Start both backend and frontend in development mode on Windows

REM Check if we're in the right directory
if not exist "run_api.py" (
    echo Error: run_api.py not found. Please run this script from the project root.
    exit /b 1
)

echo Starting backend API server on http://localhost:8000
start "Inkling Backend" cmd /k python run_api.py

REM Wait a moment for backend to start
timeout /t 2 /nobreak >nul

echo Starting frontend development server on http://localhost:3000
cd frontend
start "Inkling Frontend" cmd /k npm start

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit (this will NOT stop the servers)
pause >nul

