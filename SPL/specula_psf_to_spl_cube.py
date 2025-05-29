import os
import glob
from pathlib import Path
import numpy as np
from astropy.io import fits
from tqdm import tqdm

def process_psf_files(base_path):
    """
    Process PSF fits files from multiple timestamp folders.
    
    Parameters:
    -----------
    base_path : str
        Base path containing the timestamp folders
    """
    # Get all timestamp folders
    timestamp_folders = glob.glob(os.path.join(base_path, "*"))
    
    # First, count total number of PSF files to process
    total_psf_files = 0
    for folder in timestamp_folders:
        if os.path.isdir(folder):
            # Check if folder already has cropped files
            if not glob.glob(os.path.join(folder, "psf*_crop.fits")):
                psf_files = glob.glob(os.path.join(folder, "psf*.fits"))
                total_psf_files += len([f for f in psf_files if "_crop.fits" not in f])
    
    print(f"\nTotal PSF files to process: {total_psf_files}")
    
    # Create progress bar for total files
    with tqdm(total=total_psf_files, desc="Processing PSF files") as pbar:
        for folder in timestamp_folders:
            if not os.path.isdir(folder):
                continue
                
            # Skip folders that already have cropped files
            if glob.glob(os.path.join(folder, "psf*_crop.fits")):
                print(f"\nSkipping folder {os.path.basename(folder)} - already processed")
                continue
                
            print(f"\nProcessing folder: {os.path.basename(folder)}")
            
            # Find all PSF fits files in the current folder
            psf_files = glob.glob(os.path.join(folder, "psf*.fits"))
            
            for psf_file in psf_files:
                # Skip already processed files
                if "_crop.fits" in psf_file:
                    continue
                    
                try:
                    # Read the fits file
                    with fits.open(psf_file) as hdul:
                        # Get the data cube
                        data = hdul[0].data
                        
                        # Get the center coordinates
                        center_y = data.shape[1] // 2
                        center_x = data.shape[2] // 2
                        
                        # Calculate crop boundaries (100x100 pixels)
                        y_start = center_y - 50
                        y_end = center_y + 50
                        x_start = center_x - 50
                        x_end = center_x + 50
                        
                        # Crop the data
                        cropped_data = data[:, y_start:y_end, x_start:x_end]
                        
                        # Create output filename
                        output_file = psf_file.replace(".fits", "_crop.fits")
                        
                        # Save the cropped data
                        hdu = fits.PrimaryHDU(cropped_data)
                        hdu.writeto(output_file, overwrite=True)
                        
                except Exception as e:
                    print(f"Error processing {psf_file}: {str(e)}")
                
                # Update progress bar
                pbar.update(1)

def reorganize_cubes(base_path):
    """
    Reorganize the cropped PSF cubes by differential piston values.
    
    Parameters:
    -----------
    base_path : str
        Base path containing the timestamp folders
    """
    # Create output directory for reorganized cubes
    output_dir = os.path.join(base_path, "specula_cubes")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all timestamp folders
    timestamp_folders = glob.glob(os.path.join(base_path, "*"))
    
    # Find all cropped PSF files across all folders
    all_cropped_files = []
    for folder in timestamp_folders:
        if os.path.isdir(folder) and "specula_cubes" not in folder:
            cropped_files = glob.glob(os.path.join(folder, "psf*_crop.fits"))
            all_cropped_files.extend(cropped_files)
    
    if not all_cropped_files:
        print("No cropped files found!")
        return
        
    print(f"\nFound {len(all_cropped_files)} cropped files across all folders")
    
    # Read first file to get dimensions
    with fits.open(all_cropped_files[0]) as hdul:
        first_data = hdul[0].data
        n_pistons = first_data.shape[0]
        cube_size = first_data.shape[1:]
    
    # Create arrays to store wavelength information
    wavelengths = []
    for file in all_cropped_files:
        # Extract wavelength from filename (assuming format psfXXX_crop.fits)
        wavelength = int(os.path.basename(file).split('psf')[1].split('_')[0])
        wavelengths.append(wavelength)
    
    wavelengths = sorted(list(set(wavelengths)))  # Remove duplicates and sort
    n_wavelengths = len(wavelengths)
    
    print(f"Found {n_wavelengths} unique wavelengths: {wavelengths}")
    print(f"Reading {len(all_cropped_files)} files...")
    
    # Pre-load all data into memory
    all_data = {}
    for file in tqdm(all_cropped_files, desc="Loading files"):
        wavelength = int(os.path.basename(file).split('psf')[1].split('_')[0])
        with fits.open(file) as hdul:
            all_data[wavelength] = hdul[0].data
    
    print("Creating and saving cubes...")
    # Process each differential piston value
    for piston_idx in tqdm(range(n_pistons), desc="Creating cubes"):
        # Create a cube for this piston value
        piston_cube = np.zeros((n_wavelengths, *cube_size), dtype=first_data.dtype)
        
        # Fill the cube with data from each wavelength
        for w_idx, wavelength in enumerate(wavelengths):
            piston_cube[w_idx] = all_data[wavelength][piston_idx]
        
        # Save the reorganized cube
        output_file = os.path.join(output_dir, f"image_{piston_idx:04d}.fits")
        hdu = fits.PrimaryHDU(piston_cube)
        hdu.writeto(output_file, overwrite=True)
    
    # Clear memory
    del all_data

def main():
    # Base path containing the timestamp folders
    base_path = r"G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula\20250408"
    
    # First process all PSF files (crop them)
    process_psf_files(base_path)
    
    # Then reorganize the cropped cubes
    reorganize_cubes(base_path)

if __name__ == "__main__":
    main()
