

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

# From itertools recipes
def batched(iterable, n):
    "Batch data into lists of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            return
        yield batch


def _crop_to_valid(data):
    valid = ~np.isnan(data)

    if not np.any(valid):
        raise ValueError("No valid pixels!")

    y_indices, x_indices = np.where(valid)
    y_min, y_max = y_indices.min(), y_indices.max()
    x_min, x_max = x_indices.min(), x_indices.max()

    return data[y_min:y_max+1, x_min:x_max+1]

def load_all_files(path: os.PathLike) -> Iterator:
    '''Load FITS data from all filenames matching a given path pattern'''
    path = 'alpao820if/20250829_150620*/wavefront.fits'
    filelist = glob.glob(path)
    for filename in sorted(filelist, key=lambda x: int(os.path.dirname(x).split('_')[-1])):
        print('Generating:', filename)
        data = fits.getdata(filename)
        if data.ndim == 2:
            yield data
        elif data.ndim == 3:
            for i in range(data.shape[0]):
                yield data[i]


def cube_diff(images: Iterator, preview=False) -> Iterator:
    '''Given a stream of images, diff images in pairs'''
    for up, down in batched(images, 2):
        yield up-down
        if preview: # Only first diff for preview
            break


def smooth_image(image):
    '''Gaussian 2D smoothing'''
    kernel = Gaussian2DKernel(x_stddev=2)
    return convolve_fft(image, kernel, boundary='full', nan_treatment='interpolate')


def stack_mask(images: Iterator, save_path: os.PathLike=None, preview=False):
    '''Sum multiple images and return common mask'''
    if preview:
        ref_image = sum(islice(images, 2))
    else:
        ref_image = sum(images)
    mask = np.isnan(ref_image).astype(int)
    if save_path:
        fits.writeto(save_path, mask, overwrite=True)
        print(f'Mask saved to {save_path}')
    return mask

def apply_mask(image, maskpath: os.PathLike):
    '''mask an image'''
    mask = fits.getdata(maskpath)
    result = image * (1-mask)
    return result


def threshold(image, th_level: float=0.1):
    '''Threshold an image'''
    valid = ~np.isnan(image)
    image = image - (image * valid).max() * th_level
    positive = (image > 0).astype(int)
    return image * positive


def crop_and_resize(image, rows: int, cols: int):
    '''Crop image to illuminated portion and resize to target shape'''
    cropped = _crop_to_valid(image)
    return resize(cropped, (rows, cols), order=3, mode="reflect", anti_aliasing=True, preserve_range=True)


def stack_images(images: Iterator, save_path: os.PathLike=None, preview=False):
    '''Stack images into a 3D array'''
    if preview:
        stack = np.stack(list(islice(images, 2)))
    else:
        stack = np.stack(list(images))
    if save_path:
        fits.writeto(save_path, stack, overwrite=True)
        print(f'Stack saved to {save_path}')    




