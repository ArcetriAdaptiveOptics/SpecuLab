# Installing Specula Package

This guide helps you install the `specula` package, which is required for running PSF simulations.

## Problem: pycairo Build Failure

The `specula` package depends on `pycairo`, which requires the Cairo graphics library. On Windows, building `pycairo` from source often fails because Cairo needs to be installed separately.

## Solution: Install pycairo from Conda-Forge First

The easiest solution is to install `pycairo` from conda-forge (which provides pre-built binaries) before installing `specula`.

### Step 1: Activate Your Environment

```powershell
conda activate speculab-spl
```

### Step 2: Install pycairo from Conda-Forge

```powershell
conda install -c conda-forge pycairo
```

This installs a pre-built version of pycairo that doesn't require compiling from source.

### Step 3: Install Specula Dependencies

**Important**: The `orthogram` package requires `pycairo==1.21.0`, which will cause pip to try building from source. We need to install it carefully:

```powershell
cd "G:\My Drive\SPECULA"

# Install dependencies that don't require pycairo
pip install numpy scipy astropy matplotlib numba astro-seeing symao flask-socketio python-socketio requests

# Install orthogram WITHOUT its dependencies (to avoid pycairo rebuild)
pip install orthogram --no-deps

# Then manually install orthogram's other dependencies (excluding pycairo)
# Note: orthogram requires networkx<3.0.0, so we need to downgrade if needed
pip install PyYAML Shapely cassowary "networkx<3.0.0,>=2.8.4"
```

### Step 4: Install Specula

Now install specula itself:

```powershell
# Install specula without dependencies (to avoid pycairo rebuild)
pip install -e . --no-deps
```

**Complete installation sequence:**

```powershell
cd "G:\My Drive\SPECULA"

# Step 1: Install basic dependencies
pip install numpy scipy astropy matplotlib numba astro-seeing symao flask-socketio python-socketio requests

# Step 2: Install orthogram without dependencies
pip install orthogram --no-deps

# Step 2b: Install orthogram's dependencies (downgrade networkx if needed)
pip install PyYAML Shapely cassowary "networkx<3.0.0,>=2.8.4"

# Step 3: Install specula without dependencies
pip install -e . --no-deps
```

The `-e` flag installs it in "editable" mode, so changes to the source code are immediately reflected.

## Alternative: If Conda Install Fails

If conda doesn't have pycairo available, you can try:

### Option 1: Install Cairo Manually

1. Download Cairo for Windows from: https://www.cairographics.org/download/
2. Or use a package manager like vcpkg or MSYS2
3. Then install pycairo with pip

### Option 2: Skip pycairo (if not essential)

If `pycairo` is not essential for your use case, you might be able to modify the `specula` package to make it optional. Check the specula source code to see if pycairo is actually required.

### Option 3: Use Pre-built Wheels

Check if there are pre-built wheels available for your Python version:

```powershell
pip install --only-binary :all: pycairo
```

## Verification

After installation, verify that specula is installed correctly:

```powershell
python -c "import specula; print('Specula installed successfully!')"
```

## Troubleshooting

- **Dependency version conflicts**: You may see warnings about version mismatches:
  - `networkx`: We downgrade to `<3.0.0` to match orthogram's requirements
  - `pycairo`: orthogram requires `==1.21.0`, but conda installs `1.28.0`. This is usually fine as pycairo is backward compatible. If you encounter issues, you can try downgrading: `conda install -c conda-forge "pycairo=1.21.0"`

- **Still getting build errors**: Make sure you have Visual Studio Build Tools installed (required for compiling Python packages on Windows)

- **Conda not found**: Make sure conda is in your PATH or use the full path to conda

- **Permission errors**: Try running PowerShell as Administrator

- **Version conflicts persist**: If you continue to see dependency conflicts, you can check what's installed:
  ```powershell
  pip list | findstr "networkx pycairo"
  ```

