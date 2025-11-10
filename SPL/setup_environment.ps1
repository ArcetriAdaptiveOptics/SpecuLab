# PowerShell script to set up SpecuLab SPL environment
# This script helps you create and activate a Python virtual environment

Write-Host "Setting up SpecuLab SPL environment..." -ForegroundColor Green

# Check if conda is available
$condaAvailable = Get-Command conda -ErrorAction SilentlyContinue

if ($condaAvailable) {
    Write-Host "Conda detected. Creating conda environment..." -ForegroundColor Yellow
    conda env create -f environment.yml
    Write-Host "`nTo activate the environment, run:" -ForegroundColor Cyan
    Write-Host "  conda activate speculab-spl" -ForegroundColor White
} else {
    Write-Host "Conda not found. Creating Python virtual environment..." -ForegroundColor Yellow
    
    # Create virtual environment
    python -m venv venv
    
    Write-Host "`nVirtual environment created. Activating..." -ForegroundColor Yellow
    
    # Activate virtual environment
    .\venv\Scripts\Activate.ps1
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
    Write-Host "`nTo activate the environment in the future, run:" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
}

Write-Host "`nNote: You may need to install the 'specula' package separately." -ForegroundColor Yellow
Write-Host "Check the project documentation for installation instructions." -ForegroundColor Yellow

