

import os
import glob
import numpy as np
from astropy.io import fits
from astropy.convolution import convolve_fft, Gaussian2DKernel
from skimage.transform import resize

from decorators import Pipe, parallel_yield
from decorators import StartPipe  # Needed for import by main program

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

@Pipe
def list_all_files():
    '''Generate all IF filenames'''
    filelist = glob.glob(params.path)
    for filename in sorted(filelist, key=lambda x: int(os.path.dirname(x).split('_')[-1])):
        print(filename)
        yield filename

@Pipe
def cube_diff(filenames):
    '''Given filenames, generate all up-down IF images'''
    for filename in filenames:
        cube = fits.getdata(filename)
        for i in range(0, len(cube), 2):
            print(i)
            yield cube[i] - cube[i+1]

@Pipe
@parallel_yield
def smooth_image(image):
    '''Image gaussian smoothing'''
    kernel = Gaussian2DKernel(x_stddev=2)
    return convolve_fft(image, kernel, boundary='full', nan_treatment='interpolate')

@Pipe
def calc_mask(images):
    '''Sum multiple images and return common mask'''
    ref_image = sum(images)
    return np.isnan(ref_image).astype(int)

@Pipe
@parallel_yield
def apply_mask(image):
    '''mask an image'''
    mask = params.mask
    return image * (1-mask)

@Pipe
@parallel_yield
def threshold(image):
    '''Threshold an image'''
    mask = params.mask

    image -= (image * (1-mask)).max() * 0.1
    positive = (image > 0).astype(int)
    return image * positive

@Pipe
@parallel_yield
def crop_and_resize(image):
    '''Crop image to illuminated portion and resize to targe shape'''
    cropped = _crop_to_valid(image)
    return resize(cropped, params.target_shape, order=3, mode="reflect", anti_aliasing=True, preserve_range=True)

@Pipe
def stack_images(images):
    '''Stack images into a 3D array'''
    return np.stack(list(images))




