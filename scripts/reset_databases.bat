@echo off
REM ============================================
REM Reset Databases Script for Windows
REM ============================================
REM Usage:
REM   reset_databases.bat          - Reset all databases
REM   reset_databases.bat mongodb  - Reset only MongoDB
REM   reset_databases.bat milvus   - Reset only Milvus/Zilliz
REM ============================================

echo.
echo ================================================
echo    NotebookLM Clone - Database Reset Tool
echo ================================================
echo.

cd /d "%~dp0\.."

REM Check if venv exists
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Run the Python script with arguments
if "%1"=="" (
    backend\venv\Scripts\python.exe scripts\reset_databases.py --all
) else if "%1"=="mongodb" (
    backend\venv\Scripts\python.exe scripts\reset_databases.py --mongodb
) else if "%1"=="milvus" (
    backend\venv\Scripts\python.exe scripts\reset_databases.py --milvus
) else if "%1"=="all" (
    backend\venv\Scripts\python.exe scripts\reset_databases.py --all
) else (
    echo [ERROR] Unknown option: %1
    echo Usage: reset_databases.bat [mongodb^|milvus^|all]
    pause
    exit /b 1
)

echo.
pause
