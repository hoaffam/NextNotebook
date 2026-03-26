@echo off
REM ============================================
REM Start Application Script for Windows
REM ============================================
REM Starts both Backend and Frontend servers
REM ============================================

echo.
echo ================================================
echo    NotebookLM Clone - Application Starter
echo ================================================
echo.

cd /d "%~dp0\.."

REM Check if MongoDB is running
echo [1/4] Checking MongoDB...
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo       MongoDB is running
) else (
    echo       [WARNING] MongoDB is not running!
    echo       Please start MongoDB first: mongod
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 1
)

REM Check if venv exists
echo.
echo [2/4] Checking Python environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo       [ERROR] Virtual environment not found!
    echo       Creating virtual environment...
    cd backend
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt
    cd ..
) else (
    echo       Virtual environment OK
)

REM Check if node_modules exists
echo.
echo [3/4] Checking Node.js dependencies...
if not exist "frontend\node_modules" (
    echo       [INFO] Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
) else (
    echo       Node modules OK
)

echo.
echo [4/4] Starting servers...
echo.
echo ================================================
echo    Starting Backend (http://localhost:8000)
echo    Starting Frontend (http://localhost:5173)
echo ================================================
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Start backend in new window
start "NotebookLM Backend" cmd /k "cd /d %~dp0\..\backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in new window
start "NotebookLM Frontend" cmd /k "cd /d %~dp0\..\frontend && npm run dev"

echo.
echo Servers started in separate windows!
echo.
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Frontend:     http://localhost:5173
echo.
echo Close this window to keep servers running,
echo or close the server windows to stop them.
echo.
pause
