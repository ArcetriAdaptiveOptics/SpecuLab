import numpy as np
import glob
import astropy.io.fits as fits
import os
import argparse
import matplotlib.pyplot as plt
from tqdm import tqdm

def get_piston_values_from_fits(parent_folder):
    """
    Attempts to read piston values from FITS files in the parent folder.
    Checks for Differential_piston.fits file or reads from FITS headers.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.

    Returns:
    numpy.ndarray or None: Array of piston values if found, None otherwise.
    """
    # First check for Differential_piston.fits file
    piston_file = os.path.join(parent_folder, "Differential_piston.fits")
    if os.path.exists(piston_file):
        try:
            with fits.open(piston_file) as hdul:
                piston_values = hdul[0].data
                if piston_values is not None:
                    print(f"Found piston values in {piston_file}")
                    return piston_values
        except Exception as e:
            print(f"Warning: Could not read piston values from {piston_file}: {e}")

    # Try to read from first available FITS file header
    timestamped_folders = sorted(glob.glob(os.path.join(parent_folder, "2025*")))
    for folder in timestamped_folders:
        # Try _crop.fits first, then standard .fits
        fits_files = sorted(glob.glob(os.path.join(folder, "psf*_crop.fits")))
        if not fits_files:
            fits_files = sorted(glob.glob(os.path.join(folder, "psf*.fits")))
            fits_files = [f for f in fits_files if "_crop.fits" not in f]
        
        if fits_files:
            try:
                with fits.open(fits_files[0]) as hdul:
                    header = hdul[0].header
                    # Check for piston-related keywords
                    if 'PSTMIN' in header and 'PSTMAX' in header:
                        pst_min = header['PSTMIN']
                        pst_max = header['PSTMAX']
                        pst_step = header.get('PSTSTP', 5)  # Default step of 5
                        cube_data = hdul[0].data
                        if cube_data is not None:
                            piston_axis_size = cube_data.shape[0]
                            piston_values = np.linspace(pst_min, pst_max, piston_axis_size)
                            print(f"Found piston values from FITS header: {pst_min} to {pst_max} (step: {pst_step})")
                            return piston_values
            except Exception as e:
                print(f"Warning: Could not read piston values from FITS header: {e}")
            break  # Only check first folder
    
    return None


def extract_central_row_at_piston(parent_folder, piston_value=-6000, num_rows_to_accumulate=1, piston_values=None):
    """
    Extracts and sums central rows from FITS files at a specified piston value.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    piston_value (float): Desired piston value.
    num_rows_to_accumulate (int): Number of central rows to sum.
    piston_values (numpy.ndarray, optional): Array of piston values. If None, will be inferred from data.

    Returns:
    tuple: (wavelengths, extracted_data) where extracted_data is 2D (y = wavelengths, x = pixels).
    """
    timestamped_folders = sorted(glob.glob(os.path.join(parent_folder, "2025*")))  # Modify pattern if needed
    if not timestamped_folders:
        print("No timestamped folders found!")
        return None, None

    wavelengths = []
    extracted_data = []
    inferred_piston_values = None

    for folder in timestamped_folders:
        # First try to find _crop.fits files
        fits_files = sorted(glob.glob(os.path.join(folder, "psf*_crop.fits")))
        use_crop = True
        
        # If no _crop.fits files found, fall back to standard .fits files
        if not fits_files:
            fits_files = sorted(glob.glob(os.path.join(folder, "psf*.fits")))
            use_crop = False
            # Filter out any _crop.fits files that might have been found
            fits_files = [f for f in fits_files if "_crop.fits" not in f]
        
        if not fits_files:
            print(f"No FITS files found in {folder}")
            continue  # Skip if no FITS files found

        for file in fits_files:
            filename = os.path.basename(file)
            # Extract wavelength based on file type
            if use_crop:
                wavelength = int(filename.replace("psf", "").replace("_crop.fits", ""))
            else:
                wavelength = int(filename.replace("psf", "").replace(".fits", ""))

            if wavelength not in wavelengths:
                wavelengths.append(wavelength)

            with fits.open(file) as hdul:
                cube_data = hdul[0].data  # Assuming data is in primary HDU
                piston_axis_size = cube_data.shape[0]

                # Use provided piston_values or infer from data
                if piston_values is not None:
                    # Use provided piston values, but ensure they match the data size
                    if len(piston_values) == piston_axis_size:
                        file_piston_values = piston_values
                    else:
                        print(f"Warning: Piston values length ({len(piston_values)}) doesn't match data size ({piston_axis_size}). Inferring from data.")
                        file_piston_values = np.linspace(-6000, 6000, piston_axis_size)
                else:
                    # Infer piston values from data (default behavior)
                    if inferred_piston_values is None:
                        # Try to read from header first
                        header = hdul[0].header
                        if 'PSTMIN' in header and 'PSTMAX' in header:
                            pst_min = header['PSTMIN']
                            pst_max = header['PSTMAX']
                            inferred_piston_values = np.linspace(pst_min, pst_max, piston_axis_size)
                        else:
                            # Default: assume -6000 to +6000
                            inferred_piston_values = np.linspace(-6000, 6000, piston_axis_size)
                    file_piston_values = inferred_piston_values

                # Find the closest piston value index
                piston_idx = np.argmin(np.abs(file_piston_values - piston_value))
                image = cube_data[piston_idx]  # Select the image at the closest piston value
                #plt.imshow(image)
                #plt.show()
                
                center_y = image.shape[0] // 2
                start_row = center_y - num_rows_to_accumulate // 2
                end_row = start_row + num_rows_to_accumulate
                # Ensure row indices are within bounds
                start_row = max(0, start_row)
                end_row = min(image.shape[0], end_row)

                if start_row >= end_row: # case where num_rows_to_accumulate might be 0 or invalid
                    print(f"Warning: No rows to accumulate for Wavelength {wavelength} with num_rows_to_accumulate={num_rows_to_accumulate}. Using central row.")
                    central_profile = image[center_y, :]
                else:
                    central_profile = np.sum(image[start_row:end_row, :], axis=0)
                
                #plt.plot(central_profile)
                #plt.show()
                extracted_data.append(central_profile)

    if extracted_data:
        extracted_data = np.array(extracted_data)
        sorted_indices = np.argsort(wavelengths)
        wavelengths = np.array(wavelengths)[sorted_indices]
        extracted_data = extracted_data[sorted_indices, :]

        extracted_data = extracted_data.T  # Invert so wavelengths are on y-axis

    else:
        extracted_data = None

    return wavelengths, extracted_data


def process_all_piston_values(parent_folder, output_folder="Fringes", num_rows_to_accumulate=1, 
                               piston_min=None, piston_max=None, piston_step=None, piston_values=None):
    """
    Iterates over all piston values and saves extracted data as FITS files.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    output_folder (str): Name of the folder where output FITS files will be saved.
    num_rows_to_accumulate (int): Number of central rows to sum in extraction.
    piston_min (float, optional): Minimum piston value. If None, will try to read from FITS or use default.
    piston_max (float, optional): Maximum piston value. If None, will try to read from FITS or use default.
    piston_step (float, optional): Step size for piston values. If None, will try to read from FITS or use default.
    piston_values (numpy.ndarray, optional): Explicit array of piston values. Overrides other parameters if provided.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Determine piston values: explicit array > read from FITS > command-line args > defaults
    if piston_values is None:
        # Try to read from FITS files first
        piston_values = get_piston_values_from_fits(parent_folder)
        
        # If not found in FITS, use provided range or defaults
        if piston_values is None:
            if piston_min is None:
                piston_min = -6000
            if piston_max is None:
                piston_max = 6000
            if piston_step is None:
                piston_step = 5
            
            # Generate piston values array
            piston_values = np.arange(piston_min, piston_max + piston_step, piston_step)
            print(f"Using piston values: {piston_min} to {piston_max} with step {piston_step}")
        else:
            print(f"Using piston values from FITS files: {len(piston_values)} values from {piston_values[0]:.1f} to {piston_values[-1]:.1f}")
    else:
        print(f"Using provided piston values: {len(piston_values)} values from {piston_values[0]:.1f} to {piston_values[-1]:.1f}")
    all_filenames = []
    processed_wavelengths = None # To store wavelengths from the first successful extraction

    for i, piston_value in enumerate(tqdm(piston_values, desc="Processing Piston Values")):
        #print(f"Processing piston value {piston_value} nm ({i+1}/{len(piston_values)})...")

        wavelengths, extracted_data = extract_central_row_at_piston(parent_folder, piston_value, num_rows_to_accumulate, piston_values)

        if extracted_data is not None and extracted_data.size > 0:
            if processed_wavelengths is None and wavelengths is not None and len(wavelengths) > 0:
                processed_wavelengths = wavelengths # Store wavelengths from first valid data

            # Normalize extracted_data to 0-1 range
            min_val = np.min(extracted_data)
            max_val = np.max(extracted_data)
            if max_val > min_val: # Avoid division by zero if data is flat
                normalized_data = (extracted_data - min_val) / (max_val - min_val)
            else:
                normalized_data = extracted_data # Or np.zeros_like(extracted_data) if appropriate

            # Create FITS header
            hdr = fits.Header()
            if processed_wavelengths is not None and len(processed_wavelengths) > 0:
                hdr['WAVMIN'] = (np.min(processed_wavelengths), "Minimum wavelength (nm)")
                hdr['WAVMAX'] = (np.max(processed_wavelengths), "Maximum wavelength (nm)")
                if len(processed_wavelengths) > 1:
                    hdr['WAVSTP'] = (processed_wavelengths[1] - processed_wavelengths[0], "Wavelength step (nm)")
                else:
                    hdr['WAVSTP'] = (0, "Wavelength step (nm)") # Or some other default if only one wavelength
            else: # Fallback if wavelengths are somehow not available
                hdr['WAVMIN'] = ('UNKNOWN', "Minimum wavelength (nm)")
                hdr['WAVMAX'] = ('UNKNOWN', "Maximum wavelength (nm)")
                hdr['WAVSTP'] = ('UNKNOWN', "Wavelength step (nm)")
            hdr['PSTVAL'] = (piston_value, "Piston value (nm)")
            
            # Save the normalized 2D data as a FITS file with header
            fringe_filename = os.path.join(output_folder, f"Fringe_{i:05d}.fits")
            fits.writeto(fringe_filename, normalized_data, header=hdr, overwrite=True)
            all_filenames.append(fringe_filename)
        elif extracted_data is None:
            print(f"No data extracted for piston value {piston_value}. Skipping file save.")
        elif extracted_data.size == 0:
            print(f"Empty data extracted for piston value {piston_value}. Skipping file save.")


    # Save wavelengths and piston values as FITS files
    if processed_wavelengths is not None:
        fits.writeto(os.path.join(output_folder, "Lambda.fits"), np.array(processed_wavelengths), overwrite=True)

    fits.writeto(os.path.join(output_folder, "Differential_piston.fits"), piston_values, overwrite=True)

    print("Processing complete! All FITS files saved in:", output_folder)


def createFringes():
    parser = argparse.ArgumentParser(description="Process PSF FITS files and extract central row over piston values.")
    parser.add_argument("parent_folder", type=str, help="Path to the folder containing timestamped subdirectories.")
    parser.add_argument("--output_folder", type=str, default="Fringes", help="Folder to save output FITS files (default: Fringes).")
    parser.add_argument("--num_rows", type=int, default=1, help="Number of central rows to sum during extraction (default: 1).")
    parser.add_argument("--piston_min", type=float, default=None, help="Minimum piston value in nm (default: read from FITS or -6000).")
    parser.add_argument("--piston_max", type=float, default=None, help="Maximum piston value in nm (default: read from FITS or 6000).")
    parser.add_argument("--piston_step", type=float, default=None, help="Step size for piston values in nm (default: read from FITS or 5).")
    parser.add_argument("--piston_file", type=str, default=None, help="Path to FITS file containing piston values array (overrides other piston options).")

    args = parser.parse_args()

    # If piston_file is provided, read piston values from it
    piston_values = None
    if args.piston_file:
        if os.path.exists(args.piston_file):
            try:
                with fits.open(args.piston_file) as hdul:
                    piston_values = hdul[0].data
                    if piston_values is not None:
                        print(f"Loaded piston values from {args.piston_file}")
                    else:
                        print(f"Warning: No data found in {args.piston_file}")
            except Exception as e:
                print(f"Error reading piston values from {args.piston_file}: {e}")
                return
        else:
            print(f"Error: Piston file {args.piston_file} not found.")
            return

    process_all_piston_values(args.parent_folder, args.output_folder, args.num_rows, 
                             args.piston_min, args.piston_max, args.piston_step, piston_values)


if __name__ == "__main__":
    createFringes()