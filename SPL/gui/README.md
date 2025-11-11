# SPL GUI Application

A graphical user interface for the SPL (Spectral Pupil) calibration workflow using tkinter.

## Features

The GUI provides a tabbed interface for each step of the SPL calibration workflow:

1. **Create Mask** - Generate a circular mask with optional gap
2. **Create IF Func (Optional)** - Generate DM influence function
3. **Set Parameters** - Configure and generate YAML parameter file
4. **Run Simulation** - Execute the SPECULA PSF simulation
5. **Create Fringes** - Extract fringe patterns from PSF files

## Installation

The GUI uses tkinter, which is included with Python. Additional dependencies are listed in `requirements.txt`:

```powershell
pip install -r requirements.txt
```

## Usage

### Launch the GUI

From the `SPL` directory, run:

```powershell
python gui/run_gui.py
```

Or directly:

```powershell
python -m gui.main
```

### Workflow

1. **Create Mask Tab**: 
   - Enter pixel pupil size, gap fraction, clock angle, and filename
   - Click "Create Mask" to generate the mask file

2. **Create IF Func Tab** (Optional):
   - Enter pixel pupil size and IF filename
   - Click "Create IF Function" to generate the influence function

3. **Set Parameters Tab**:
   - Configure all simulation parameters
   - Set wavelength range, piston scan parameters, mask/IF references, and storage directory
   - Click "Generate YAML File" to create the parameter file

4. **Run Simulation Tab**:
   - Select the generated YAML parameter file
   - Optionally enable CPU mode
   - Click "Run Simulation" to start the simulation
   - Monitor progress in the output window
   - Use "Stop Simulation" to cancel if needed

5. **Create Fringes Tab**:
   - Select the parent folder containing PSF files
   - Set output folder and optional parameters
   - Piston values are auto-detected from FITS files if not specified
   - Click "Create Fringes" to extract fringe patterns

## Notes

- The GUI runs all operations in separate threads to keep the interface responsive
- Status messages appear in the status bar at the bottom of the window
- File browsers are available for selecting folders and files
- Input validation ensures correct parameter types and ranges
- The simulation tab shows real-time output from the simulation process

## Troubleshooting

- **Import Errors**: Make sure you're running from the SPL directory and all dependencies are installed
- **Matplotlib Display**: The GUI uses a non-interactive backend for matplotlib to prevent blocking
- **File Paths**: Use forward slashes or double backslashes in Windows paths
- **Simulation Output**: Check the output text area in the simulation tab for detailed error messages

