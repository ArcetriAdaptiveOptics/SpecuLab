

from itertools import islice
import os
import glob
import numpy as np
from astropy.io import fits
from astropy.convolution import convolve_fft, Gaussian2DKernel
from skimage.transform import resize


from typing import Iterator

class Params():
    pass
params = Params()


def _crop_to_valid(data):
    valid = ~np.isnan(data)

    if not np.any(valid):
        raise ValueError("No valid pixels!")

    y_indices, x_indices = np.where(valid)
    y_min, y_max = y_indices.min(), y_indices.max()
    x_min, x_max = x_indices.min(), x_indices.max()

    return data[y_min:y_max+1, x_min:x_max+1]

def list_all_files(path: os.PathLike) -> Iterator:
    '''Generate all filenames matching a given path pattern'''
    path = 'alpao820if/20250829_150620*/wavefront.fits'
    filelist = glob.glob(path)
    print(filelist)
    for filename in sorted(filelist, key=lambda x: int(os.path.dirname(x).split('_')[-1])):
        print('Generating:', filename)
        yield filename


def cube_diff(filenames: Iterator, preview=False) -> Iterator:
    '''Given filenames, generate all up-down IF images'''
    for filename in filenames:
        print('Got filename:', filename)
        cube = fits.getdata(filename)
        for i in range(0, len(cube), 2):
            print('Generating cube', i)
            yield cube[i] - cube[i+1]
            if preview: # Only first diff for preview
                break


def smooth_image(image):
    '''Gaussian 2D smoothing'''
    print('Smoothing image')
    kernel = Gaussian2DKernel(x_stddev=2)
    return convolve_fft(image, kernel, boundary='full', nan_treatment='interpolate')


def calc_mask(images: Iterator, preview=False):
    '''Sum multiple images and return common mask'''
    if preview:
        print('Mask preview')
        ref_image = sum(islice(images, 2))
    else:
        ref_image = sum(images)
    return np.isnan(ref_image).astype(int)


def apply_mask(image, maskpath: os.PathLike):
    '''mask an image'''
    mask = fits.getdata(maskpath)
    result = image * (1-mask)
    return result


def threshold(image, th_level=0.1):
    '''Threshold an image'''
    valid = ~np.isnan(image)
    image -= (image * valid).max() * th_level
    positive = (image > 0).astype(int)
    return image * positive


def crop_and_resize(image, rows, cols):
    '''Crop image to illuminated portion and resize to target shape'''
    cropped = _crop_to_valid(image)
    return resize(cropped, (rows, cols), order=3, mode="reflect", anti_aliasing=True, preserve_range=True)


def stack_images(images: Iterator, preview=False):
    '''Stack images into a 3D array'''
    if preview:
        return np.stack(list(islice(images, 2)))
    else:
        return np.stack(list(images))




