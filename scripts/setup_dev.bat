@echo off
REM Quick setup script for Second Brain Agent development environment (Windows)

echo ==================================
echo Second Brain Agent - Dev Setup
echo ==================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo pip upgraded
echo.

REM Install production dependencies
echo Installing production dependencies...
pip install -r requirements.txt
echo Production dependencies installed
echo.

REM Install development dependencies
echo Installing development dependencies...
pip install -r requirements-dev.txt
echo Development dependencies installed
echo.

REM Install pre-commit hooks
echo Installing pre-commit hooks...
pre-commit install
echo Pre-commit hooks installed
echo.

REM Create necessary directories
echo Creating project directories...
if not exist logs mkdir logs
if not exist output mkdir output
echo Directories created
echo.

echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo Next steps:
echo 1. Activate venv: venv\Scripts\activate
echo 2. Copy .env.example to .env and add your API keys
echo 3. Run tests: pytest tests/
echo 4. Start coding!
echo.
echo Available commands (use make or run manually):
echo   pytest tests/           Run tests
echo   black src/ tests/       Format code
echo   flake8 src/ tests/      Run linter
echo.
pause
