import numpy as np
import glob
import astropy.io.fits as fits
import os
import argparse
import matplotlib.pyplot as plt

def extract_central_row_at_piston(parent_folder, piston_value=-6000):
    """
    Extracts the central row from FITS files at a specified piston value.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    piston_value (float): Desired piston value.

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
        fits_files = sorted(glob.glob(os.path.join(folder, "psf*.fits")))  # Get all psfXXX.fits files
        if not fits_files:
            print(f"No FITS files found in {folder}")
            continue  # Skip if no FITS files found

        for file in fits_files:
            filename = os.path.basename(file)
            wavelength = int(filename.replace("psf", "").replace(".fits", ""))

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
                central_row = image[image.shape[0] // 2, :]  # Extract middle row
                #plt.plot(central_row)
                #plt.show()
                extracted_data.append(central_row)

    if extracted_data:
        extracted_data = np.array(extracted_data)
        sorted_indices = np.argsort(wavelengths)
        wavelengths = np.array(wavelengths)[sorted_indices]
        extracted_data = extracted_data[sorted_indices, :]

        extracted_data = extracted_data.T  # Invert so wavelengths are on y-axis

    else:
        extracted_data = None

    return wavelengths, extracted_data


def process_all_piston_values(parent_folder, output_folder="Fringes"):
    """
    Iterates over all piston values (-6000 to +6000 nm in 5 nm steps) and saves
    extracted data as FITS files.

    Parameters:
    parent_folder (str): Path to the parent folder containing timestamped subdirectories.
    output_folder (str): Name of the folder where output FITS files will be saved.
    """
    os.makedirs(output_folder, exist_ok=True)

    piston_values = np.arange(-6000, 6005, 5)  # Piston values from -6000 to +6000 nm
    all_filenames = []

    for i, piston_value in enumerate(piston_values):
        print(f"Processing piston value {piston_value} nm ({i+1}/{len(piston_values)})...")

        wavelengths, extracted_data = extract_central_row_at_piston(parent_folder, piston_value)

        if extracted_data is not None:
            # Save the extracted 2D data as a FITS file
            fringe_filename = os.path.join(output_folder, f"Fringe_{i:05d}.fits")
            fits.writeto(fringe_filename, extracted_data, overwrite=True
                         
                         )
            all_filenames.append(fringe_filename)

    # Save wavelengths and piston values as FITS files
    if wavelengths is not None:
        fits.writeto(os.path.join(output_folder, "Lambda.fits"), np.array(wavelengths), overwrite=True)

    fits.writeto(os.path.join(output_folder, "Differential_piston.fits"), piston_values, overwrite=True)

    print("Processing complete! All FITS files saved in:", output_folder)


def createFringes():
    parser = argparse.ArgumentParser(description="Process PSF FITS files and extract central row over piston values.")
    parser.add_argument("parent_folder", type=str, help="Path to the folder containing timestamped subdirectories.")
    parser.add_argument("--output_folder", type=str, default="Fringes", help="Folder to save output FITS files (default: Fringes).")

    args = parser.parse_args()

    process_all_piston_values(args.parent_folder, args.output_folder)


if __name__ == "__main__":
    createFringes()