
# **SPECULA Calibration with SPL**

This guide helps you calibrate the SPL (Spectral Pupil) with SPECULA by walking you through the necessary steps, from generating the gap mask to extracting fringe patterns from PSF simulations.

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
  total_time:        2401.0               # Total iterations (calculated as piston p2v / piston step + 1)
  time_step:         1.0                  # Time step for each iteration
  display_server:    false                # Whether or not to display the server output

pupilstop:
  class: 'Pupilstop'
  input_mask_data: 'mymask'               # Name of your generated mask file (w/o .fits)

ramp:
  class: 'FuncGenerator'
  func_type: 'LINEAR'
  slope: [5]                              # Piston step (e.g., 5 nm)
  constant: [-6000]                       # Initial piston value. Final piston = total_time * slope + constant

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
- Adjust `slope` and `constant` under the `ramp` section to match the desired piston values.
- Modify `store_dir` to the correct path where you want the data to be saved.

#### **3. Generate the `.yml` File for the PSF Simulation**

Once the parameters are set, you can generate the `.yml` file and run the SPECULA code to get the simulated PSFs. To do this:

1. Open **PowerShell**.
2. Navigate to the `.\main\SPL\` directory.
3. Run the following command:

```powershell
& "C:\Program Files\Git\bin\bash.exe" "G:\My Drive\SPECULA\main\SPL\runAll.sh"
```

#### **4. Generate Fringe Patterns from PSF Files**

Once the simulated PSFs are ready, you can generate the fringe patterns using the `create_fringes.py` script. To do this:

1. Open **PowerShell**.
2. Run the following command:

```powershell
python .\create_fringes.py 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula' --output_folder 'G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula\Fringes'
```

- Replace the first path (`G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula`) with the folder where your input PSF files are located.
- The `--output_folder` option specifies the directory where the fringe patterns will be saved (e.g., `Fringes` folder).

---

### **Output Folder Structure**

After completing the above steps, your output folder (`Fringes`) will contain the following files:

```
- Fringes/
  - Fringe_00000.fits
  - Fringe_00001.fits
  - ...
  - wavelengths.fits        # Wavelength data
  - Differential_piston.fits # Piston values used for extraction
```

---

### **Troubleshooting**

- **Missing Dependencies**: If you encounter errors related to missing Python packages, you can install them with:

  ```bash
  pip install numpy astropy matplotlib
  ```

- **Incorrect Paths**: Ensure that all paths (e.g., for your PSF files, output folder, and data storage) are correct and accessible.

- **Permissions Issues**: Check if you have the required permissions to read from and write to the specified directories.

---

### **License**

This code is provided under the [MIT License](LICENSE).
