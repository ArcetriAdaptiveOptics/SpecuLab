
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
from astropy.convolution import convolve, Gaussian2DKernel
from skimage.transform import resize

import multiprocessing as mp

def crop_to_valid(data):
    mask = np.isnan(data)
    valid = ~mask

    if not np.any(valid):
        raise ValueError("No valid pixels!")

    y_indices, x_indices = np.where(valid)
    y_min, y_max = y_indices.min(), y_indices.max()
    x_min, x_max = x_indices.min(), x_indices.max()

    data[mask] = 0
    return data[y_min:y_max+1, x_min:x_max+1]


def list_all_files():
    import glob
    filelist = glob.glob('alpao820if/20250829_104714_*/wavefront.fits')
    for filename in sorted(filelist)[:2]:
        print(filename)
        yield filename

def cube_diff(filenames):
    for filename in filenames:
        cube = fits.getdata(filename)
        for i in range(0, len(cube), 2):
            print(i)
            yield cube[i+1] - cube[i]

def smooth_image(images):
    with mp.Pool(16) as p:
        for result in p.imap(myconvolve, images):
            yield result
        
kernel = Gaussian2DKernel(x_stddev=2)
def myconvolve(image):
    return convolve(image, kernel, boundary='extend', nan_treatment='interpolate')

def calc_mask(images):
    for i, image in enumerate(images):
        if i == 0:
            ref_image = image.copy()
        else:
            ref_image += image
    yield np.isnan(ref_image).astype(int)

def apply_mask(images):
    global mask
    for image in images:
        image[mask] = 0
        yield image

def threshold(images):
    for image in images:
      #  image -= image[~mask].max() * 0.1
      #  image[image < 0] = 0
        yield image

def crop_and_resample(images):
    target_shape=(512,512)
    for image in images:
        cropped = crop_to_valid(image)
        resampled = resize(cropped, target_shape, order=3, mode="reflect", anti_aliasing=True, preserve_range=True)
        yield resampled


# Mask calcalation
stream1 = list_all_files()
stream2 = cube_diff(stream1)
stream3 = smooth_image(stream2)
stream4 = calc_mask(stream3)

mask = np.stack(list(stream4))
fits.writeto('mask.fits', mask, overwrite=True)

# Full calculation
stream1 = list_all_files()
stream2 = cube_diff(stream1)
stream3 = apply_mask(stream2)
stream4 = smooth_image(stream3)
stream5 = threshold(stream4)
stream6 = crop_and_resample(stream5)

ifunc = np.stack(list(stream6))
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




