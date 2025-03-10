import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import os
import sys

class createDmInfluenceFunction:
    def __init__(self, size=3200, filename='step_response_output.fits'):
        self.size = size
        self.filename = os.path.join(".\\calib\\data", filename)
        self._influence_function = self.generate_step_response()
        self._mask_inf_func = np.ones((size, size))  # Mask filled with ones

    def generate_step_response(self):
        # Create an array where the left side is 0 and the right side is 1
        step_response = np.zeros((self.size, self.size))
        step_response[:, self.size // 2:] = 1  # Set right half to 1
        return step_response

    def save_step_response(self):
        # Flatten the 2D influence function into a 1D array
        flattened_influence_function = self._influence_function.flatten()

        # Calculate NAXIS1 dynamically as size * size
        naxis1 = self.size * self.size
        naxis2 = 1  # Only one row (1D)

        # Create the FITS header with required fields
        hdr = fits.Header()
        hdr['SIMPLE'] = True  # Conforms to FITS standard
        hdr['BITPIX'] = -32  # Data type is 32-bit floating point
        hdr['NAXIS'] = 2  # Two-dimensional data
        hdr['NAXIS1'] = naxis1  # Set NAXIS1 to size * size (dynamic)
        hdr['NAXIS2'] = naxis2  # Set NAXIS2 to 1
        hdr['EXTEND'] = True  # Indicates that the file contains extensions

        # Create the primary HDU and append the data as (1, size * size)
        hdu = fits.PrimaryHDU(header=hdr)
        hdul = fits.HDUList([hdu])

        # Append the influence function (1, size * size array) as an extension
        hdul.append(fits.ImageHDU(data=flattened_influence_function.reshape(1, -1), name='PRIMARY'))

        # Ensure the directory exists
        dir_path = os.path.dirname(self.filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Save the file and return the full path
        hdul.writeto(self.filename, overwrite=True)
        return os.path.abspath(self.filename)

    def save_mask_piston(self):
        # Create a 2D array filled with ones (mask)
        mask_piston = np.ones((self.size, self.size))

        # Create the FITS header with required fields
        hdr = fits.Header()
        hdr['SIMPLE'] = True  # Conforms to FITS standard
        hdr['BITPIX'] = -32  # Data type is 32-bit floating point
        hdr['NAXIS'] = 2  # Two-dimensional data
        hdr['NAXIS1'] = self.size  # Set NAXIS1 to size
        hdr['NAXIS2'] = self.size  # Set NAXIS2 to size
        hdr['EXTEND'] = True  # Indicates that the file contains extensions

        # Create the primary HDU and append the data as (size, size)
        hdu = fits.PrimaryHDU(header=hdr)
        hdul = fits.HDUList([hdu])

        # Append the mask piston data (size, size array) as an extension
        hdul.append(fits.ImageHDU(data=mask_piston, name='PRIMARY'))

        # Ensure the directory exists
        dir_path = os.path.dirname(self.filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Generate the filename for the mask piston FITS file
        mask_filename = os.path.join(os.path.dirname(self.filename), f'mask_piston_{self.size}.fits')
        
        # Save the file and return the full path
        hdul.writeto(mask_filename, overwrite=True)
        return os.path.abspath(mask_filename)

    def display_step_response(self):
        # Display the step response in 2D using matplotlib
        plt.imshow(self._influence_function, cmap='gray', origin='lower')
        plt.colorbar(label='Intensity')
        plt.title('Step Response (2D)')
        plt.show()

def main():
    # Check if arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python create_dm_ifunc.py <size> <filename>")
        sys.exit(1)
    
    # Parse command-line arguments
    size = int(sys.argv[1])
    filename = sys.argv[2]

    # Create an instance of createDmInfluenceFunction
    step_response = createDmInfluenceFunction(size=size, filename=filename)

    # Display the step response
    step_response.display_step_response()

    # Save and get the full path of the FITS file for the step response
    saved_file_path = step_response.save_step_response()
    print(f"Step response FITS file saved at: {saved_file_path}")

    # Save and get the full path of the FITS file for the mask piston
    mask_piston_file_path = step_response.save_mask_piston()
    print(f"Mask piston FITS file saved at: {mask_piston_file_path}")

if __name__ == "__main__":
    main()
