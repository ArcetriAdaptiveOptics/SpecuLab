
# **SPECULA Calibration with SPL**

This guide helps you calibrate the SPL (Spectral Pupil) with SPECULA by walking you through the necessary steps, from generating the gap mask to extracting fringe patterns from PSF simulations.

---

## **Environment Setup**

Before running any scripts, you need to set up a Python environment with the required dependencies.

### **Option 1: Using Conda (Recommended)**

If you have Conda installed:

1. Open **PowerShell** or **Command Prompt**.
2. Navigate to the `SPL` directory.
3. Create and activate the environment:

```powershell
conda env create -f environment.yml
conda activate speculab-spl
```

### **Option 2: Using Python Virtual Environment**

If you don't have Conda:

1. Open **PowerShell**.
2. Navigate to the `SPL` directory.
3. Run the setup script:

```powershell
.\setup_environment.ps1
```

Or manually:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### **Option 3: Manual Installation**

If you prefer to install dependencies manually:

```powershell
pip install numpy astropy matplotlib tqdm scipy scikit-image
```

### **Installing the Specula Package**

The `specula` package is required for running simulations but needs to be installed separately. 

**Important**: The `specula` package depends on `pycairo`, which can be difficult to build on Windows. We recommend installing `pycairo` from conda-forge first:

```powershell
# Activate your environment first
conda activate speculab-spl

# Install pycairo from conda-forge (pre-built, no compilation needed)
conda install -c conda-forge pycairo

# Then install specula dependencies carefully (orthogram requires pycairo==1.21.0)
cd "G:\My Drive\SPECULA"

# Install basic dependencies
pip install numpy scipy astropy matplotlib numba astro-seeing symao flask-socketio python-socketio requests

# Install orthogram without dependencies (to avoid pycairo rebuild)
pip install orthogram --no-deps

# Install orthogram's dependencies (downgrade networkx to <3.0.0 as required)
pip install PyYAML Shapely cassowary "networkx<3.0.0,>=2.8.4"

# Finally install specula
pip install -e . --no-deps
```

For detailed installation instructions and troubleshooting, see [INSTALL_SPECULA.md](INSTALL_SPECULA.md).

### **Optional: GPU Acceleration**

If you have a CUDA-capable GPU and want to use GPU acceleration (for `cupy`):

```powershell
# For CUDA 11.x
pip install cupy-cuda11x

# For CUDA 12.x
pip install cupy-cuda12x
```

**Note:** The `create_spl_mask.py` script uses `cupy` for GPU acceleration. If you don't have a GPU or `cupy` installed, you may need to modify the script to use `numpy` instead.

---

### **Steps to Calibrate SPL with SPECULA**

#### **1. Generate the Gap Mask and DM IF**

Before proceeding with the calibration, you need to generate a mask for the pupil. To do this:

1. Open **PowerShell**.
2. Navigate to the `.\main\SPL\` directory.
3. Run the following command:

```powershell
python .\create_spl_mask.py `pixel_pupil` --gap `gap_fraction` --clock_angle  `clock_angle` --filename "mymask"
```

- `pixel_pupil`: The number of pixels in the pupil (same as the mask size).
- `gap_fraction`: The fraction of the gap within the pupil.
- `clock_angle`: The angle of the gap (0° for vertical, 90° for horizontal).

4. Then you need also to generate an influence function with the same sampling of the pupil. To do this:

```powershell
python .\create_dm_ifunc.py `pixel_pupil` `filename.fits`
```

- `pixel_pupil`: The number of pixels in the pupil (same as the mask size).
- `filename.fits`: The filename of the IF (include .fits extension).

#### **2. Set Piston Scan Parameters in `generate_multiwave_yml.py`**

You will need to configure several parameters in the `generate_multiwave_yml.py` file. Specifically, you'll need to edit the following processing objects and the data store section at the end.

Modify the following fields:

```yaml
main:
  root_dir:          '.\calib'           # Directory containing your calibration data
  pixel_pupil:       80                   # Number of pixels (same as your mask)
  pixel_pitch:       0.0001               # Pixel pitch in meters per pixel
  total_time:        2401.0               # Total iterations (calculated as WF piston p2v / WF piston step + 1)
  time_step:         1.0                  # Time step for each iteration
  display_server:    false                # Whether or not to display the server output

pupilstop:
  class: 'Pupilstop'
  input_mask_data: 'mymask'               # Name of your generated mask file (w/o .fits)

ramp:
  class: 'FuncGenerator'
  func_type: 'LINEAR'
  slope: [5]                              # WF piston step (e.g., 5 nm)
  constant: [-6000]                       # Initial WF piston value. Final WF piston = total_time * slope + constant

ifunc:
  class: 'IFunc'
  ifunc_data: 'ifunc_piston_80'         # Name of your generated DM influence function file (w/o .fits)
  mask_data: 'mask_piston_80'           # Name of your generated DM mask array file (w/o .fits)

# Data store section
data_store:
  class: 'DataStore'
  store_dir: 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula'  # Path to store data
  inputs:
    input_list: [
      # Insert wavelengths list here
    ]
```

- Ensure `input_mask_data` points to the name of your mask.
- Adjust `slope` and `constant` under the `ramp` section to match the desired WF piston values.
- Modify `store_dir` to the correct path where you want the data to be saved.

#### **3. Generate the `.yml` File for the PSF Simulation**

Once the parameters are set, you can generate the `.yml` file and run the SPECULA code to get the simulated PSFs. To do this:

1. Open **PowerShell**.
2. Navigate to the `SPL` directory.
3. Run the script using one of the following methods:

**Option A: Using PowerShell Script (Recommended)**

```powershell
.\runAll.ps1
```

**Option B: Using Bash (if Git Bash is installed)**

```powershell
# First, check if Git Bash is installed
$bashPath = "C:\Program Files\Git\bin\bash.exe"
if (Test-Path $bashPath) {
    & $bashPath "$PWD\runAll.sh"
} else {
    Write-Host "Git Bash not found. Please use Option A or install Git for Windows."
}
```

**Option C: Run commands manually**

You can also run the Python commands directly in PowerShell:

```powershell
python generate_multiwave_yml.py 720 730 5
python main_simul.py params_spl_multiwave.yml
```

#### **4. Generate Fringe Patterns from PSF Files**

Once the simulated PSFs are ready, you can generate the fringe patterns using the `create_fringes.py` script. To do this:

1. Open **PowerShell**.
2. Run the following command:

**Basic Usage (Auto-detect piston values from FITS files):**

```powershell
python .\create_fringes.py 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula' --output_folder 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula\Fringes'
```

**With Custom Piston Range:**

```powershell
python .\create_fringes.py 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula' --output_folder 'Fringes' --piston_min -5000 --piston_max 5000 --piston_step 10
```

**Using Piston Values from a FITS File:**

```powershell
python .\create_fringes.py 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula' --output_folder 'Fringes' --piston_file 'Differential_piston.fits'
```

**Command-Line Options:**

- `parent_folder` (required): Path to the folder containing timestamped subdirectories with PSF files.
- `--output_folder` (optional, default: `Fringes`): Directory where the fringe patterns will be saved.
- `--num_rows` (optional, default: `1`): Number of central rows to sum during extraction.
- `--piston_min` (optional): Minimum piston value in nm. If not specified, the script will:
  1. Try to read from `Differential_piston.fits` in the parent folder
  2. Try to read from FITS headers (`PSTMIN`, `PSTMAX`, `PSTSTP` keywords)
  3. Use default value of -6000 nm
- `--piston_max` (optional): Maximum piston value in nm. If not specified, follows the same detection logic as `--piston_min` (default: 6000 nm).
- `--piston_step` (optional): Step size for piston values in nm. If not specified, follows the same detection logic (default: 5 nm).
- `--piston_file` (optional): Path to a FITS file containing piston values array. This option overrides all other piston-related options.

**Piston Value Detection Priority:**

The script determines piston values in the following order (highest to lowest priority):

1. `--piston_file` option (if provided)
2. `Differential_piston.fits` file in the parent folder
3. FITS header keywords (`PSTMIN`, `PSTMAX`, `PSTSTP`) from PSF files
4. Command-line arguments (`--piston_min`, `--piston_max`, `--piston_step`)
5. Default values (-6000 to 6000 nm with 5 nm step)

**Notes:**

- The script automatically checks for `_crop.fits` files first, then falls back to standard `.fits` files if cropped versions are not found.
- If piston values are found in FITS files, the script will use them automatically without requiring command-line arguments.
- Replace the example paths with your actual paths to PSF files and output directory.

---

### **Output Folder Structure**

After completing the above steps, your output folder (`Fringes`) will contain the following files:

```
- Fringes/
  - Fringe_00000.fits
  - Fringe_00001.fits
  - ...
  - wavelengths.fits        # Wavelength data
  - Differential_piston.fits # WF piston values used for extraction
```

---

### **Troubleshooting**

- **Missing Dependencies**: If you encounter errors related to missing Python packages, ensure your environment is activated and install dependencies:

  ```powershell
  pip install -r requirements.txt
  ```

- **Environment Not Activated**: Make sure you've activated your environment before running scripts:
  - Conda: `conda activate speculab-spl`
  - Virtual env: `.\venv\Scripts\Activate.ps1`

- **Cupy/GPU Issues**: If you encounter issues with `cupy` in `create_spl_mask.py`, you can modify the script to use `numpy` instead by replacing `cupy` imports with `numpy`.

- **Bash Script Issues**: If you can't run bash from PowerShell:
  - **Solution 1**: Use the PowerShell script instead: `.\runAll.ps1`
  - **Solution 2**: Check if Git Bash is installed. The default path is `C:\Program Files\Git\bin\bash.exe`. If Git is installed elsewhere, update the path.
  - **Solution 3**: Install Git for Windows from https://git-scm.com/download/win
  - **Solution 4**: Run the Python commands directly in PowerShell (see Option C in Step 3)

- **PowerShell Execution Policy**: If you get an execution policy error when running `.ps1` scripts:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Incorrect Paths**: Ensure that all paths (e.g., for your PSF files, output folder, and data storage) are correct and accessible.

- **Permissions Issues**: Check if you have the required permissions to read from and write to the specified directories.

---

### **License**

This code is provided under the [MIT License](LICENSE).
