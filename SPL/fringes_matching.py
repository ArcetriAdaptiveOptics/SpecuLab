import os
import numpy as np
from astropy.io import fits
from scipy import signal
from skimage.registration import phase_cross_correlation
from skimage.feature import match_template
import matplotlib
matplotlib.use('Agg')  # Set a non-interactive backend BEFORE importing pyplot
import matplotlib.pyplot as plt
import re
import argparse

def is_image_normalized(image, epsilon=1e-6):
    """Check if image is normalized to range [0-epsilon, 1+epsilon]."""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return False # Cannot determine for empty or invalid data
    
    img_min = np.min(image)
    img_max = np.max(image)
    
    # Handles flat images as well. If img_min == img_max, it checks if that value is in [0,1]
    if img_min >= (0.0 - epsilon) and img_max <= (1.0 + epsilon):
        return True
    return False

def load_fits_image_and_header(file_path):
    """Load a FITS file and return its data array and header."""
    with fits.open(file_path) as hdul:
        # Assuming the data is in the primary HDU
        return hdul[0].data, hdul[0].header

def load_lambda_array(lambda_file_path):
    """Load the Lambda.fits file containing wavelength array for templates."""
    if not os.path.exists(lambda_file_path):
        print(f"Error: Lambda file not found at {lambda_file_path}")
        return None
    try:
        with fits.open(lambda_file_path) as hdul:
            return hdul[0].data
    except Exception as e:
        print(f"Error loading lambda file {lambda_file_path}: {e}")
        return None

def normalize_image(image):
    """Normalize image to range [0, 1]."""
    if image is None or image.size == 0:
        return image # Or handle as an error/empty image
    img_min = np.min(image)
    img_max = np.max(image)
    if img_max > img_min:
        return (image - img_min) / (img_max - img_min)
    # Handle flat images (all pixels same value)
    # Current behavior: flat images become all zeros.
    # If img_min == img_max, it returns np.zeros_like(image).
    return np.zeros_like(image) if img_min == img_max else image # Note: 'else image' is unreachable here.

def match_fringe_pattern(target_image_normalized, template_images, are_templates_pre_normalized, method='cross_correlation'):
    """
    Match a target fringe pattern with a repository of template images.
    Assumes target_image_normalized is already normalized and wavelength-cropped.
    Templates are wavelength-cropped. are_templates_pre_normalized indicates if template set is considered normalized.
    """
    match_scores = []
    
    if target_image_normalized is None or target_image_normalized.shape[0] == 0 or target_image_normalized.shape[1] == 0:
        print("Error: Target image for matching is empty or invalid.")
        return -1, [] # Indicate error

    # Target image is already normalized by the caller (main function)
    target_norm = target_image_normalized
    
    for template in template_images:
        if template is None or template.shape[0] == 0 or template.shape[1] == 0:
            match_scores.append(-np.inf) # Penalize invalid templates
            continue

        # Conditionally normalize the template based on the check performed on the first template
        if are_templates_pre_normalized:
            template_norm = normalize_image(template)
        else:
            template_norm = template # Use as-is, warning was issued by load_all_templates
        
        # Ensure same dimensions for matching by cropping to the smallest overlapping region
        # This is after wavelength cropping has already aligned them spectrally.
        min_rows = min(target_norm.shape[0], template_norm.shape[0])
        min_cols = min(target_norm.shape[1], template_norm.shape[1])
        
        target_crop = target_norm[:min_rows, :min_cols]
        template_crop = template_norm[:min_rows, :min_cols]

        if target_crop.size == 0 or template_crop.size == 0:
            match_scores.append(-np.inf)
            continue
        
        if method == 'cross_correlation':
            # Compute normalized cross-correlation
            # Ensure inputs are 1D for corrcoef if they are not already
            target_flat = target_crop.flatten()
            template_flat = template_crop.flatten()
            if target_flat.size != template_flat.size or target_flat.size == 0:
                match_scores.append(-np.inf) # Should not happen if min_rows/cols > 0
                continue
            # np.corrcoef can return nan if one of the inputs has zero variance (e.g. flat image)
            correlation_matrix = np.corrcoef(target_flat, template_flat)
            if np.isnan(correlation_matrix).any() or correlation_matrix.shape != (2,2):
                 correlation = -np.inf # Penalize
            else:
                correlation = correlation_matrix[0, 1]
            match_scores.append(correlation)
            
        elif method == 'template_matching':
            # Template matching
            # match_template requires template to be smaller than image
            if template_crop.shape[0] > target_crop.shape[0] or template_crop.shape[1] > target_crop.shape[1]:
                # If template is larger, try to match target as template in template_crop
                # This case should ideally be handled by the min_rows/min_cols cropping,
                # but as a fallback:
                if target_crop.shape[0] <= template_crop.shape[0] and target_crop.shape[1] <= template_crop.shape[1]:
                     result = match_template(template_crop, target_crop)
                else: # Cannot make them compatible for match_template
                    match_scores.append(-np.inf)
                    continue
            else:
                result = match_template(target_crop, template_crop)
            
            if result.size > 0:
                match_scores.append(np.max(result))
            else:
                match_scores.append(-np.inf) # Penalize if result is empty
    
    if not match_scores: # No valid templates or all comparisons failed
        return -1, match_scores

    best_match_idx = np.argmax(match_scores)
    
    # Check if all scores were -inf (no good match)
    if match_scores[best_match_idx] == -np.inf:
        return -1, match_scores

    return best_match_idx, match_scores

def load_all_templates(template_dir, target_min_wave, target_max_wave, template_lambda_values):
    """Load all Fringe_*.fits templates, cropped to target wavelength range.
    Checks the first loaded template for normalization.
    Returns: templates_data, template_paths, skipped_files, are_templates_pre_normalized (bool)
    """
    templates_data = []
    template_paths = []
    skipped_files = 0
    fringe_pattern = re.compile(r'Fringe_\d+\.fits$')
    
    first_template_checked_for_norm = False
    are_templates_pre_normalized = True # Assume true until checked

    if template_lambda_values is None or template_lambda_values.size == 0:
        print("Error: Template lambda array is missing or empty. Cannot crop templates.")
        return [], [], 0, are_templates_pre_normalized

    # Find column indices in template_lambda_values for cropping
    template_col_start_idx = np.searchsorted(template_lambda_values, target_min_wave, side='left')
    template_col_end_idx = np.searchsorted(template_lambda_values, target_max_wave, side='right') -1 # searchsorted 'right' gives insertion point, so -1 for inclusive end

    if template_col_start_idx > template_col_end_idx or template_col_start_idx >= len(template_lambda_values) or template_col_end_idx < 0:
        print(f"Warning: Target wavelength range [{target_min_wave:.2f}-{target_max_wave:.2f} nm] does not overlap with template wavelength data or is invalid.")
        return [], [], 0, are_templates_pre_normalized
    
    # Ensure indices are within the bounds of template_lambda_values
    template_col_start_idx = max(0, template_col_start_idx)
    template_col_end_idx = min(len(template_lambda_values) - 1, template_col_end_idx)

    if template_col_start_idx > template_col_end_idx: # Check again after clamping
        print(f"Warning: Clamped target wavelength range [{template_lambda_values[template_col_start_idx]:.2f}-{template_lambda_values[template_col_end_idx]:.2f} nm] is invalid after clamping for templates.")
        return [], [], 0, are_templates_pre_normalized

    num_template_cols_to_crop = template_col_end_idx - template_col_start_idx + 1
    if num_template_cols_to_crop <= 0:
        print(f"Warning: No template columns fall within the target wavelength range [{target_min_wave:.2f}-{target_max_wave:.2f} nm].")
        return [], [], 0, are_templates_pre_normalized
    
    #print(f"Scanning directory: {template_dir}")
    
    sorted_filenames = sorted(os.listdir(template_dir)) # Ensure consistent order for first template check

    for filename in sorted_filenames:
        if fringe_pattern.match(filename):
            file_path = os.path.join(template_dir, filename)
            try:
                # Assuming load_fits_image_and_header now just returns data for templates
                image_data, _ = load_fits_image_and_header(file_path) # We don't need header for individual templates here
                
                if image_data is None or not isinstance(image_data, np.ndarray) or image_data.ndim != 2:
                    #print(f"Skipping {filename}: Not a 2D numpy array or empty data")
                    skipped_files += 1
                    continue
                
                # Check normalization of the first valid template loaded
                if not first_template_checked_for_norm:
                    if image_data.size > 0: # Ensure there's data to check
                        if not is_image_normalized(image_data):
                            print(f"Warning: The first loaded template fringe ('{filename}') appears to be not normalized (not in [0,1] range). All templates from this set will be used as-is without on-the-fly normalization.")
                            are_templates_pre_normalized = False
                        # else: # First template is normalized, no message needed, flag remains True
                        first_template_checked_for_norm = True
                    # If image_data.size is 0, we can't check norm, so we wait for the next valid template
                
                # Crop the template according to the wavelength range
                if image_data.shape[1] < num_template_cols_to_crop : # check if template has enough columns
                     #print(f"Skipping {filename}: Template has fewer columns ({image_data.shape[1]}) than determined by Lambda.fits indices ({num_template_cols_to_crop}). Potentially inconsistent Lambda.fits or template.")
                     # This check is tricky if Lambda.fits is universal but templates vary in width.
                     # The critical part is that template_col_start_idx and template_col_end_idx are valid for image_data
                     if template_col_end_idx >= image_data.shape[1]:
                         #print(f"Skipping {filename}: template_col_end_idx {template_col_end_idx} out of bounds for template shape {image_data.shape[1]}")
                         skipped_files += 1
                         continue
                
                cropped_template = image_data[:, template_col_start_idx : template_col_end_idx + 1]

                if cropped_template.shape[1] == 0:
                    #print(f"Skipping {filename}: Resulted in 0 columns after wavelength cropping.")
                    skipped_files += 1
                    continue
                
                templates_data.append(cropped_template)
                template_paths.append(file_path)
                
            except Exception as e:
                #print(f"Error loading or cropping template {file_path}: {e}")
                skipped_files += 1
    
    #print(f"Found {len(templates_data)} valid Fringe templates after wavelength cropping, skipped {skipped_files} files")
    
    return templates_data, template_paths, skipped_files, are_templates_pre_normalized

def load_differential_piston_value(best_template_path):
    """
    Load the differential piston value from 'Differential_piston.fits'
    using the ID from the best_template_path as an index.
    """
    try:
        template_dir_of_match = os.path.dirname(best_template_path)
        piston_file_path = os.path.join(template_dir_of_match, "Differential_piston.fits")

        if not os.path.exists(piston_file_path):
            #print(f"Info: Differential_piston.fits not found at {piston_file_path}")
            return None

        match_id_search = re.search(r"Fringe_(\d+)\.fits", os.path.basename(best_template_path))
        if not match_id_search:
            #print(f"Warning: Could not extract ID from template filename: {os.path.basename(best_template_path)}")
            return None
        fringe_id = int(match_id_search.group(1))

        with fits.open(piston_file_path) as hdul:
            piston_array = hdul[0].data
            
            if not isinstance(piston_array, np.ndarray) or piston_array.ndim != 1:
                #print(f"Warning: Differential_piston.fits data in {piston_file_path} is not a 1D NumPy array.")
                return None

            if fringe_id >= len(piston_array):
                #print(f"Warning: Fringe ID {fringe_id} is out of bounds for piston array of length {len(piston_array)} in {piston_file_path}")
                return None
            return piston_array[fringe_id]

    except ValueError:
        #print(f"Warning: Could not convert fringe ID to integer from {os.path.basename(best_template_path)}")
        return None
    except Exception as e:
        piston_file_path_for_error = os.path.join(os.path.dirname(best_template_path), "Differential_piston.fits") if 'best_template_path' in locals() else "Differential_piston.fits"
        #print(f"Error loading differential piston value from {piston_file_path_for_error}: {e}")
        return None

def plot_best_match(target_image, best_template, target_name, template_name, piston_value, output_dir, method_name):
    """Plot the target image and the best matching template side by side, with piston value, and save to specified dir."""
    
    if target_image is None or best_template is None or target_image.size == 0 or best_template.size == 0:
        #print(f"Skipping plot for {method_name} due to empty target or template.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    ax1.imshow(normalize_image(target_image), cmap='viridis')
    ax1.set_title(f"Target: {target_name} (Wavelength Cropped)")
    ax1.axis('off')
    
    ax2.imshow(normalize_image(best_template), cmap='viridis')
    title_str = f"Best Match: {template_name} (Wavelength Cropped)"
    if piston_value is not None:
        title_str += f"\nPiston: {piston_value:.2f} nm"
    ax2.set_title(title_str)
    ax2.axis('off')
    
    plt.tight_layout()
    
    base_target_name = os.path.splitext(os.path.basename(target_name))[0]
    output_filename = f"{base_target_name}_{method_name}_match.png"
    save_path = os.path.join(output_dir, output_filename)
    
    try:
        plt.savefig(save_path)
        #print(f"Plot saved to {save_path}")
    except Exception as e:
        print(f"Error saving plot {save_path}: {e}")
    #plt.show() # User has commented this out
    plt.close(fig) 

def main(args_in=None):
    # If args_in is None, it means the script is run directly.
    # Otherwise, it's called from analyze_batch.py
    if args_in is None:
        parser = argparse.ArgumentParser(description="Match a target FITS fringe pattern against a template library, with wavelength cropping.")
        parser.add_argument("target_fits_path", help="Path to the target Qm FITS file.")
        args = parser.parse_args()
    else:
        args = args_in # Use the arguments passed from analyze_batch.py

    target_file = args.target_fits_path
    template_dir = r"G:\Shared drives\PNRR-OAA\STILES\WP5000\Integration\SPL\Specula\Fringes\20250509" # Hardcoded for now

    try:
        full_target_data, target_header = load_fits_image_and_header(target_file)
        if full_target_data is None:
            print(f"Error: Could not load target image data from {target_file}")
            return
        #print(f"Loaded target image: {target_file}, Original shape: {full_target_data.shape}")
        
        # Check and normalize target image if needed
        if full_target_data.size > 0: # Ensure there's data to check/normalize
            if not is_image_normalized(full_target_data):
                print(f"Info: Target image '{os.path.basename(target_file)}' is not normalized. Normalizing on the fly.")
                full_target_data = normalize_image(full_target_data)
            # else: Target is already normalized, no action needed.
        
    except Exception as e:
        print(f"Error loading target FITS file {target_file}: {e}")
        return

    # Extract wavelength information from target header
    try:
        target_min_wave = float(target_header['MINCOMWV'])
        target_max_wave = float(target_header['MAXCOMWV'])
        naxis2_target = int(target_header['NAXIS2']) # Number of columns in target (wavelength axis)
        # NCOMWAVE = int(target_header['NCOMWAVE']) # Use if target needs resampling, for now assume NAXIS2 spans MIN-MAX
    except KeyError as e:
        print(f"Error: Missing wavelength keyword {e} in target header of {target_file}.")
        return
    except ValueError as e:
        print(f"Error: Invalid value for wavelength keyword in target header of {target_file}: {e}")
        return

    # Determine actual wavelengths for each column of the target image
    # Assuming NAXIS2 columns linearly span MINCOMWV to MAXCOMWV
    target_actual_wavelengths_per_column = np.linspace(target_min_wave, target_max_wave, naxis2_target)
    
    # Determine column indices for cropping the target image to MINCOMWV-MAXCOMWV range
    # (This might seem redundant if linspace is already over MINCOMWV-MAXCOMWV, but it's good for consistency
    # if the actual range covered by NAXIS2 was wider and MINCOMWV/MAXCOMWV defined a sub-region)
    target_crop_start_col = np.searchsorted(target_actual_wavelengths_per_column, target_min_wave, side='left')
    target_crop_end_col = np.searchsorted(target_actual_wavelengths_per_column, target_max_wave, side='right') - 1
    
    # Ensure indices are valid
    target_crop_start_col = max(0, target_crop_start_col)
    target_crop_end_col = min(naxis2_target - 1, target_crop_end_col)

    if target_crop_start_col > target_crop_end_col:
        print(f"Error: Target image wavelength range [{target_min_wave}-{target_max_wave}] results in invalid column indices after processing.")
        return
        
    target_image_wavelength_cropped = full_target_data[:, target_crop_start_col : target_crop_end_col + 1]
    
    if target_image_wavelength_cropped.shape[1] == 0:
        print(f"Error: Target image has 0 columns after wavelength cropping to range [{target_min_wave}-{target_max_wave} nm].")
        return
    #print(f"Target image cropped to shape: {target_image_wavelength_cropped.shape} for wavelength range [{target_min_wave}-{target_max_wave} nm]")

    # Load template lambda values
    lambda_file_path = os.path.join(template_dir, "Lambda.fits")
    template_lambda_values = load_lambda_array(lambda_file_path)
    if template_lambda_values is None:
        print("Could not load template lambda values. Exiting.")
        return

    # Load and crop template images, also get normalization status of template set
    templates, template_paths, skipped, are_templates_pre_normalized = load_all_templates(template_dir, target_min_wave, target_max_wave, template_lambda_values)
    #print(f"Loaded {len(templates)} wavelength-cropped template images, skipped {skipped}. Templates pre-normalized: {are_templates_pre_normalized}")
    
    if not templates:
        print("No valid template images found after wavelength cropping.")
        return
    
    #methods = ['cross_correlation', 'template_matching']
    methods =['cross_correlation']
    output_plot_dir = os.path.dirname(target_file)
    
    all_results = []
    final_piston_value = None # Variable to store the piston value for return

    for method in methods:
        best_idx, scores = match_fringe_pattern(target_image_wavelength_cropped, templates, are_templates_pre_normalized, method=method)
        
        if best_idx != -1 and scores: # Check for valid match
            best_template_file_path = template_paths[best_idx]
            piston_value = load_differential_piston_value(best_template_file_path)
            
            # If this is the cross_correlation method, store its piston_value
            if method == 'cross_correlation':
                final_piston_value = piston_value

            result_info = {
                "method": method,
                "best_match_file": os.path.basename(best_template_file_path),
                "score": scores[best_idx],
                "piston_nm": piston_value if piston_value is not None else "N/A"
            }
            all_results.append(result_info)
            
            print(f"Method: {method}, Best Match: {os.path.basename(best_template_file_path)}, Score: {scores[best_idx]:.4f}, Piston: {piston_value if piston_value is not None else 'N/A'}")

            plot_best_match(
                target_image_wavelength_cropped, 
                templates[best_idx],
                os.path.basename(target_file),
                os.path.basename(best_template_file_path),
                piston_value,
                output_plot_dir,
                method
            )
        else:
            print(f"Method: {method}, No valid match found or error during matching.")
            all_results.append({
                "method": method,
                "best_match_file": "N/A",
                "score": "N/A",
                "piston_nm": "N/A"
            })

    # Optional: print a summary of all results if needed
    # print("\nSummary of results:")
    # for res in all_results:
    #    print(f"  {res['method']}: Match={res['best_match_file']}, Score={res['score']}, Piston={res['piston_nm']}")
    
    return final_piston_value


if __name__ == "__main__":
    main() # Call main without arguments when run directly
