import numpy as np
import glob
import astropy.io.fits as fits
import os
import argparse
import matplotlib.pyplot as plt
from tqdm import tqdm

def extract_central_row_at_piston(parent_folder, piston_value=-6000, num_rows_to_accumulate=1):
    """
    Extracts and sums central rows from FITS files at a specified piston value.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    piston_value (float): Desired piston value.
    num_rows_to_accumulate (int): Number of central rows to sum.

    Returns:
    tuple: (wavelengths, extracted_data) where extracted_data is 2D (y = wavelengths, x = pixels).
    """
    timestamped_folders = sorted(glob.glob(os.path.join(parent_folder, "2025*")))  # Modify pattern if needed
    if not timestamped_folders:
        print("No timestamped folders found!")
        return None, None

    wavelengths = []
    extracted_data = []

    for folder in timestamped_folders:
        fits_files = sorted(glob.glob(os.path.join(folder, "psf*_crop.fits")))  # Get all psfXXX.fits files
        if not fits_files:
            print(f"No FITS files found in {folder}")
            continue  # Skip if no FITS files found

        for file in fits_files:
            filename = os.path.basename(file)
            wavelength = int(filename.replace("psf", "").replace("_crop.fits", ""))

            if wavelength not in wavelengths:
                wavelengths.append(wavelength)

            with fits.open(file) as hdul:
                cube_data = hdul[0].data  # Assuming data is in primary HDU
                piston_axis_size = cube_data.shape[0]

                # Generate piston values (assuming step of 5 nm from -6000 to +6000)
                piston_values = np.linspace(-6000, 6000, piston_axis_size)

                # Find the closest piston value index
                piston_idx = np.argmin(np.abs(piston_values - piston_value))
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


def process_all_piston_values(parent_folder, output_folder="Fringes", num_rows_to_accumulate=1):
    """
    Iterates over all piston values (-6000 to +6000 nm in 5 nm steps) and saves
    extracted data as FITS files.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    output_folder (str): Name of the folder where output FITS files will be saved.
    num_rows_to_accumulate (int): Number of central rows to sum in extraction.
    """
    os.makedirs(output_folder, exist_ok=True)

    piston_values = np.arange(-6000, 6005, 5)  # Piston values from -6000 to +6000 nm
    all_filenames = []
    processed_wavelengths = None # To store wavelengths from the first successful extraction

    for i, piston_value in enumerate(tqdm(piston_values, desc="Processing Piston Values")):
        #print(f"Processing piston value {piston_value} nm ({i+1}/{len(piston_values)})...")

        wavelengths, extracted_data = extract_central_row_at_piston(parent_folder, piston_value, num_rows_to_accumulate)

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

    args = parser.parse_args()

    process_all_piston_values(args.parent_folder, args.output_folder, args.num_rows)


if __name__ == "__main__":
    createFringes()