# Diagnostic script to check why bash might not be working from PowerShell

Write-Host "=== Bash Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host ""

# Check 1: Common Git Bash paths
Write-Host "1. Checking for Git Bash installation..." -ForegroundColor Yellow
$bashPaths = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    "$env:ProgramFiles\Git\bin\bash.exe",
    "$env:ProgramFiles(x86)\Git\bin\bash.exe"
)

$foundBash = $null
foreach ($path in $bashPaths) {
    if (Test-Path $path) {
        Write-Host "   ✓ Found Git Bash at: $path" -ForegroundColor Green
        $foundBash = $path
        break
    } else {
        Write-Host "   ✗ Not found: $path" -ForegroundColor Red
    }
}

if (-not $foundBash) {
    Write-Host ""
    Write-Host "   Git Bash not found in common locations." -ForegroundColor Yellow
    Write-Host "   Checking PATH environment variable..." -ForegroundColor Yellow
    
    # Check if bash is in PATH
    $bashInPath = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashInPath) {
        Write-Host "   ✓ Found 'bash' in PATH: $($bashInPath.Source)" -ForegroundColor Green
        $foundBash = $bashInPath.Source
    } else {
        Write-Host "   ✗ 'bash' not found in PATH" -ForegroundColor Red
    }
}

Write-Host ""

# Check 2: PowerShell execution policy
Write-Host "2. Checking PowerShell execution policy..." -ForegroundColor Yellow
$execPolicy = Get-ExecutionPolicy
Write-Host "   Current execution policy: $execPolicy" -ForegroundColor $(if ($execPolicy -ne 'Restricted') { 'Green' } else { 'Red' })

if ($execPolicy -eq 'Restricted') {
    Write-Host "   ⚠ Warning: Execution policy is Restricted. You may need to change it:" -ForegroundColor Yellow
    Write-Host "     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
}

Write-Host ""

# Check 3: Test running bash
if ($foundBash) {
    Write-Host "3. Testing bash execution..." -ForegroundColor Yellow
    try {
        $result = & "$foundBash" --version 2>&1
        Write-Host "   ✓ Bash is working!" -ForegroundColor Green
        Write-Host "   Version info: $($result[0])" -ForegroundColor Gray
    } catch {
        Write-Host "   ✗ Error running bash: $_" -ForegroundColor Red
    }
} else {
    Write-Host "3. Skipping bash test (bash not found)" -ForegroundColor Yellow
}

Write-Host ""

# Check 4: Check if runAll.sh exists
Write-Host "4. Checking for runAll.sh script..." -ForegroundColor Yellow
$parentDir = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $parentDir "runAll.sh"
if (Test-Path $scriptPath) {
    Write-Host "   ✓ Found runAll.sh at: $scriptPath" -ForegroundColor Green
} else {
    Write-Host "   ✗ runAll.sh not found at: $scriptPath" -ForegroundColor Red
}

Write-Host ""

# Recommendations
Write-Host "=== Recommendations ===" -ForegroundColor Cyan
$parentDir = Split-Path -Parent $PSScriptRoot
if ($foundBash) {
    Write-Host "✓ Git Bash is installed. You can use it with:" -ForegroundColor Green
    $bashCmd = "& `"$foundBash`" `"$parentDir\runAll.sh`""
    Write-Host "  $bashCmd" -ForegroundColor White
} else {
    Write-Host "✗ Git Bash not found. Options:" -ForegroundColor Yellow
    Write-Host "  1. Install Git for Windows: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "  2. Use the PowerShell script instead: .\runAll.ps1" -ForegroundColor White
    Write-Host "  3. Run Python commands directly in PowerShell" -ForegroundColor White
}

Write-Host ""
Write-Host "Recommended: Use .\runAll.ps1 (PowerShell script) - no bash needed!" -ForegroundColor Green

