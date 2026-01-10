#!/bin/bash
# Start both backend and frontend in development mode

# Check if we're in the right directory
if [ ! -f "run_api.py" ]; then
    echo "Error: run_api.py not found. Please run this script from the project root."
    exit 1
fi

# Start backend in background
echo "Starting backend API server on http://localhost:8000"
python run_api.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "Starting frontend development server on http://localhost:3000"
cd frontend
npm start
FRONTEND_PID=$!

# Trap to kill both processes on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for either process to exit
wait

