# Virtual Environment Setup Script
# This script creates and activates a Python virtual environment for the project

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectPath ".venv"

Write-Host "Setting up Python Virtual Environment for MyBarista..."
Write-Host "Project Path: $projectPath"
Write-Host ".venv Path: $venvPath"

# Try to find Python
$pythonCmds = @("python3", "python", "py")
$pythonFound = $false
$pythonCmd = ""

foreach ($cmd in $pythonCmds) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python") {
            Write-Host "Found Python: $cmd - $version"
            $pythonCmd = $cmd
            $pythonFound = $true
            break
        }
    }
    catch {
        # Continue to next command
    }
}

if (-not $pythonFound) {
    Write-Host "ERROR: Python is not installed or not in PATH"
    Write-Host "Please install Python 3.8+ from https://www.python.org/"
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..."
& $pythonCmd -m venv $venvPath

if (Test-Path (Join-Path $venvPath "Scripts\Activate.ps1")) {
    Write-Host "Virtual environment created successfully!"
    Write-Host "`nTo activate the virtual environment, run:"
    Write-Host ".\venv\Scripts\Activate.ps1"
    Write-Host "`nTo deactivate, run:"
    Write-Host "deactivate"
} else {
    Write-Host "ERROR: Failed to create virtual environment"
    exit 1
}

# Activate venv
Write-Host "`nActivating virtual environment..."
& (Join-Path $venvPath "Scripts\Activate.ps1")

# Upgrade pip
Write-Host "`nUpgrading pip..."
python -m pip install --upgrade pip

# Install requirements
$reqPath = Join-Path $projectPath "requirements.txt"
if (Test-Path $reqPath) {
    Write-Host "`nInstalling requirements from requirements.txt..."
    pip install -r $reqPath
    Write-Host "Successfully installed all requirements!"
} else {
    Write-Host "Warning: requirements.txt not found at $reqPath"
}

Write-Host "`nSetup complete! Your virtual environment is ready."
Write-Host "Run 'streamlit run app.py' to start the application."
