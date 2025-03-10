import cupy as cp
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import argparse
import os

def createSplMask(pixel_pupil, gap=0.0, clock_angle=0.0, filename="mymask.fits"):
    """
    Creates a circular mask that is tangent to the edges of the square pupil frame,
    with an optional zero-filled rectangular gap.

    :param pixel_pupil: Size of the square pupil frame (NxN grid).
    :param gap: Width of the rectangular gap as a fraction of the diameter.
    :param clock_angle: Angle of the gap in degrees (0° = horizontal, 90° = vertical).
    :param filename: Name of the file to save the mask.
    :return: 2D cupy array with a circular mask (1 inside the circle, 0 outside),
             with a zero-filled rectangle superimposed.
    """
    # Ensure the filename ends with '.fits'
    if not filename.endswith('.fits'):
        filename += '.fits'

    # Create coordinate grid
    y, x = cp.ogrid[-pixel_pupil//2:pixel_pupil//2, -pixel_pupil//2:pixel_pupil//2]

    # Compute radius as half the frame size (circle touches the edges)
    radius = pixel_pupil / 2

    # Create mask (1 inside the circle, 0 outside)
    mask = (x**2 + y**2) <= radius**2

    # Convert clock angle to radians
    theta = np.radians(clock_angle)

    # Convert gap width from fraction to pixel units
    gap_width = gap * pixel_pupil

    # Apply 2D rotation matrix to the grid
    x_rot = x * cp.cos(theta) + y * cp.sin(theta)
    y_rot = -x * cp.sin(theta) + y * cp.cos(theta)

    # Create rectangular gap by setting mask values to 0 inside the rotated rectangle
    mask[cp.abs(x_rot) <= (gap_width / 2)] = 0
    
    # Save mask as a FITS file
    savename = os.path.join(".\calib\data", filename)
    os.makedirs(os.path.dirname(savename), exist_ok=True)
    fits.writeto(savename, cp.asnumpy(mask.astype(float)), overwrite=True)
    print("File saved as", savename)

    # Display the mask
    plt.imshow(cp.asnumpy(mask.astype(float)), cmap='gray', origin='upper')
    plt.title(f"Circular Mask with Zero-Filled Rectangle (Gap={gap}, Angle={clock_angle}°)")
    plt.colorbar()
    plt.show()

    return mask.astype(float)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a circular mask with a gap for SPL calibration.")
    parser.add_argument("pixel_pupil", type=int, help="Size of the square pupil frame (NxN grid).")
    parser.add_argument("--gap", type=float, default=0.0, help="Width of the gap as a fraction of the diameter (default=0.0).")
    parser.add_argument("--clock_angle", type=float, default=0.0, help="Clock angle of the gap in degrees (default=0.0).")
    parser.add_argument("--filename", type=str, default="mymask.fits", help="Name of the file to save the mask (default='mymask.fits').")
    
    args = parser.parse_args()

    # Generate the mask with the given arguments
    createSplMask(args.pixel_pupil, gap=args.gap, clock_angle=args.clock_angle, filename=args.filename)
