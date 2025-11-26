#!/bin/bash

# LCBO Invoice Processor - Startup Script

echo "Starting LCBO Invoice Processor..."
echo ""

# Check if backend venv exists, if not create it
if [ ! -d "backend/venv" ]; then
    echo "Creating backend virtual environment..."
    python3 -m venv backend/venv
fi

# Activate backend venv and install dependencies
echo "Setting up backend..."
source backend/venv/bin/activate
cd backend
pip install -q -r requirements.txt
cd ..

# Start backend in background
echo "Starting backend server..."
source backend/venv/bin/activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start frontend
echo ""
echo "Starting frontend server..."
cd frontend
npm start

# Cleanup: kill backend when frontend stops
kill $BACKEND_PID 2>/dev/null
