@echo off
REM Virtual Environment Setup Script for MyBarista
REM This script creates and configures a Python virtual environment

setlocal enabledelayedexpansion

set projectPath=%~dp0
set venvPath=%projectPath%.venv

echo Setting up Python Virtual Environment for MyBarista...
echo Project Path: %projectPath%
echo .venv Path: %venvPath%

REM Try to find Python
set pythonCmd=
for %%A in (py.exe python.exe python3.exe) do (
    where /q %%A
    if !errorlevel! equ 0 (
        set pythonCmd=%%A
        echo Found Python: %%A
        goto :found
    )
)

:found
if "%pythonCmd%"=="" (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
cd /d "%projectPath%"
call %pythonCmd% -m venv venv

if exist "%venvPath%\Scripts\activate.bat" (
    echo Virtual environment created successfully!
    echo.
    echo To activate the virtual environment, run:
    echo .venv\Scripts\activate.bat
    echo.
    echo To deactivate, run:
    echo deactivate
    echo.
    echo Activating virtual environment...
    call "%venvPath%\Scripts\activate.bat"
    
    echo.
    echo Upgrading pip...
    python -m pip install --upgrade pip
    
    if exist "%projectPath%requirements.txt" (
        echo.
        echo Installing requirements from requirements.txt...
        pip install -r requirements.txt
        echo Successfully installed all requirements!
    ) else (
        echo Warning: requirements.txt not found
    )
    
    echo.
    echo Setup complete! Your virtual environment is ready.
    echo Run 'streamlit run app.py' to start the application.
) else (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

pause
