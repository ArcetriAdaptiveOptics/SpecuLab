# PowerShell script to install specula package with proper dependency handling
# This script ensures pycairo from conda is used instead of trying to build from source

Write-Host "Installing Specula package..." -ForegroundColor Green
Write-Host ""

# Check if we're in a conda environment
$condaEnv = $env:CONDA_DEFAULT_ENV
if (-not $condaEnv) {
    Write-Host "Warning: Not in a conda environment. Make sure to activate speculab-spl first:" -ForegroundColor Yellow
    Write-Host "  conda activate speculab-spl" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Check if pycairo is installed
Write-Host "Checking for pycairo installation..." -ForegroundColor Yellow
$pycairoCheck = python -c "import cairo; print('pycairo version:', cairo.version_string())" 2>&1
if ($?) {
    Write-Host "✓ pycairo is installed: $pycairoCheck" -ForegroundColor Green
} else {
    Write-Host "✗ pycairo not found. Installing from conda-forge..." -ForegroundColor Yellow
    conda install -c conda-forge pycairo -y
    if (-not $?) {
        Write-Host "Failed to install pycairo from conda. Please install manually:" -ForegroundColor Red
        Write-Host "  conda install -c conda-forge pycairo" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host ""

# Navigate to SPECULA directory
$speculaPath = "G:\My Drive\SPECULA"
if (-not (Test-Path $speculaPath)) {
    Write-Host "Error: SPECULA directory not found at: $speculaPath" -ForegroundColor Red
    Write-Host "Please update the path in this script or navigate to the SPECULA directory manually." -ForegroundColor Yellow
    exit 1
}

Write-Host "Navigating to SPECULA directory: $speculaPath" -ForegroundColor Yellow
Set-Location $speculaPath

Write-Host ""
Write-Host "Installing specula dependencies (excluding pycairo)..." -ForegroundColor Yellow

# Install basic dependencies that don't require pycairo
Write-Host "Installing basic dependencies..." -ForegroundColor Cyan
pip install numpy scipy astropy matplotlib numba astro-seeing symao flask-socketio python-socketio requests

if (-not $?) {
    Write-Host "Warning: Some dependencies failed to install. Continuing anyway..." -ForegroundColor Yellow
}

# Install orthogram without dependencies (it requires pycairo==1.21.0 which would trigger a rebuild)
Write-Host "Installing orthogram (without dependencies to avoid pycairo rebuild)..." -ForegroundColor Cyan
pip install orthogram --no-deps

# Install orthogram's other dependencies manually (excluding pycairo)
# Note: orthogram requires networkx<3.0.0, so we need to downgrade if needed
Write-Host "Installing orthogram dependencies (excluding pycairo, downgrading networkx if needed)..." -ForegroundColor Cyan
pip install PyYAML Shapely cassowary "networkx<3.0.0,>=2.8.4"

Write-Host ""
Write-Host "Installing specula in editable mode (skipping dependencies to avoid pycairo rebuild)..." -ForegroundColor Yellow
pip install -e . --no-deps

if ($?) {
    Write-Host ""
    Write-Host "✓ Specula installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verifying installation..." -ForegroundColor Yellow
    python -c "import specula; print('Specula version:', specula.__version__ if hasattr(specula, '__version__') else 'installed')"
} else {
    Write-Host ""
    Write-Host "✗ Installation failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}
