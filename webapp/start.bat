@echo off
echo Starting PDF Translation Bot Web Application...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Copy PDF translator module
echo Copying PDF translator module...
copy ..\pdf_translator.py . >nul

REM Create directories if they don't exist
if not exist uploads mkdir uploads
if not exist downloads mkdir downloads

REM Start the application
echo Starting Flask application...
echo Open your browser and navigate to http://localhost:5000
python app.py

pause
