

from astropy.io import fits
import matplotlib.pyplot as plt

from pipeline import StartPipe, list_all_files, cube_diff, smooth_image, calc_mask, apply_mask, crop_and_resize, threshold, stack_images
from pipeline import params

params.path = '/home/puglisi/cascading/alpao820if/20250829_150620*/wavefront.fits'
params.target_shape = (512, 512)

mask = StartPipe | list_all_files | cube_diff | smooth_image | calc_mask

fits.writeto('mask.fits', mask, overwrite=True)

mask = fits.getdata('mask.fits')
print(mask.shape)

# Full calculation

params.mask = mask

ifunc = StartPipe | list_all_files | cube_diff | apply_mask | smooth_image | threshold | crop_and_resize | stack_images

fits.writeto('ifunc.fits', ifunc, overwrite=True)

import sys
sys.exit(0)


plt.figure()
plt.imshow(cropped)
plt.title('smoothed and cropped')
plt.figure()
plt.imshow(resampled)
plt.title('final resampled image')
plt.figure()
plt.imshow(data)
plt.title('original')
plt.show()




