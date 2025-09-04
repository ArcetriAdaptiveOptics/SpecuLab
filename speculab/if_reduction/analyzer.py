


class StartPipe:
    pass


class Pipe:
    '''
    Functions used in pipes must be decorated with @Pipe
    '''

    def __init__(self, func):
        self.func = func

    def __ror__(self, other):
        # "other" is the input from the left side of the pipe
        if other is not StartPipe:
            return self.func(other)
        else:
            return self.func()

    def __call__(self, *args, **kwargs):
        # Allow calling the function as usual
        return self.func(*args, **kwargs)


from astropy.io import fits
import matplotlib.pyplot as plt

from pipeline import list_all_files, cube_diff, smooth_image, calc_mask, apply_mask, crop_and_resize, threshold, stack_images
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








