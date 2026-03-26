#!/bin/bash
# ============================================
# Start Application Script for Linux/Mac
# ============================================
# Starts both Backend and Frontend servers
# ============================================

echo ""
echo "================================================"
echo "   NotebookLM Clone - Application Starter"
echo "================================================"
echo ""

cd "$(dirname "$0")/.."

# Check if MongoDB is running
echo "[1/4] Checking MongoDB..."
if pgrep -x "mongod" > /dev/null; then
    echo "      MongoDB is running"
else
    echo "      [WARNING] MongoDB is not running!"
    echo "      Please start MongoDB first: mongod"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if venv exists
echo ""
echo "[2/4] Checking Python environment..."
if [ ! -f "backend/venv/bin/python" ]; then
    echo "      [INFO] Creating virtual environment..."
    cd backend
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
    cd ..
else
    echo "      Virtual environment OK"
fi

# Check if node_modules exists
echo ""
echo "[3/4] Checking Node.js dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "      [INFO] Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "      Node modules OK"
fi

echo ""
echo "[4/4] Starting servers..."
echo ""
echo "================================================"
echo "   Starting Backend (http://localhost:8000)"
echo "   Starting Frontend (http://localhost:5173)"
echo "================================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
cd backend
./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Servers started!"
echo ""
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Frontend:     http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for processes
wait
