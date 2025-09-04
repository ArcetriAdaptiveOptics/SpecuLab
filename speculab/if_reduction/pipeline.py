

from itertools import islice
import os
import glob
import numpy as np
from astropy.io import fits
from astropy.convolution import convolve_fft, Gaussian2DKernel
from skimage.transform import resize


from typing import Iterator


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
    valid = np.logical_and(~np.isnan(data), data != 0)

    if not np.any(valid):
        raise ValueError("No valid pixels!")

    y_indices, x_indices = np.where(valid)
    y_min, y_max = y_indices.min(), y_indices.max()
    x_min, x_max = x_indices.min(), x_indices.max()

    return data[y_min:y_max+1, x_min:x_max+1]

def load_all_files(path: os.PathLike) -> Iterator:
    '''Load 2D FITS data from all filenames matching a given path pattern'''
    filelist = glob.glob(path)
    if len(filelist) == 0:
        raise FileNotFoundError(path)
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

def normalize_constant(images: Iterator, constant: float) -> Iterator:
    '''Normalize all images by a constant value'''
    for image in images:
        yield image / constant


def normalize_to_vector(images: Iterator, value_vector: os.PathLike) -> Iterator:
    '''Normalize each image by a different value'''
    norm = fits.getdata(value_vector)
    for i, image in enumerate(images):
        yield image / norm[i]


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
    ref_image[np.isnan(ref_image)] = 0
    mask = (ref_image==0).astype(int)
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


def stack_images(images: Iterator,
                 save_path: os.PathLike=None,
                 preview=False) -> Iterator:
    '''Stack images into a 3D array and optionally save them'''
    stack = []
    for i, image in enumerate(images):
        stack.append(image)
        yield image
        if preview and i == 1:
            break
    stack = np.stack(list(stack))
    if save_path:
        fits.writeto(save_path, stack, overwrite=True)
        print(f'Stack saved to {save_path}')    


def modal_base(images: Iterator,
               tel_diameter_in_m: float,
               r0_in_m: float,
               L0_in_m: float,
               zern_modes: int,
               klbasis_save_path: os.PathLike,
               m2c_save_path: os.PathLike,
               s_save_path: os.PathLike,
               use_cupy=True, single_precision=True):
    '''Generate modal base'''
    if use_cupy:
        try:
            import cupy as xp
        except ImportError:
            print('Cupy not available, falling back to numpy')
            xp = np
    else:
        xp = np

    import specula
    specula.init(0)
    from specula import cpuArray
    from specula.lib.modal_base_generator import make_modal_base_from_ifs_fft

    dtype = xp.float32 if single_precision else xp.float64
    ifunc = xp.stack(map(xp.array(images))).astype(dtype)
    mask = (ifunc.sum(axis=0) != 0).astype(dtype)
    ifunc2d = ifunc[:, mask]

    klbasis, m2c, s = make_modal_base_from_ifs_fft(mask,
                                                   diameter=tel_diameter_in_m,
                                                   influence_functions=ifunc2d,
                                                   r0=r0_in_m,
                                                   L0=L0_in_m,
                                                   zern_modes=zern_modes,
                                                   xp=xp, dtype=dtype)

    fits.writeto(klbasis_save_path, cpuArray(klbasis))
    fits.writeto(m2c_save_path, cpuArray(m2c))
    fits.writeto(s_save_path, cpuArray(s))


