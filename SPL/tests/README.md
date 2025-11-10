# Tests and Diagnostics

This folder contains diagnostic and test scripts for the SpecuLab SPL project.

## Scripts

### `check_bash.ps1`

A diagnostic script to check why bash might not be working from PowerShell. It checks for:
- Git Bash installation in common locations
- PowerShell execution policy
- Bash executable functionality
- Presence of required scripts

**Usage:**
```powershell
cd "G:\My Drive\git\SpecuLab\SPL"
.\tests\check_bash.ps1
```

Or from the tests directory:
```powershell
cd "G:\My Drive\git\SpecuLab\SPL\tests"
.\check_bash.ps1
```

