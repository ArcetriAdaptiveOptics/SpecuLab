import argparse
import numpy as np

def generateMultiwaveYml(initial_wavelength, final_wavelength, wavelength_step, output_file):
    """
    Generates a YAML configuration file for PSF calculations with a range of wavelengths.

    Parameters:
    initial_wavelength (int): The starting wavelength (in nm).
    final_wavelength (int): The final wavelength (in nm).
    wavelength_step (int): The step size for wavelength increments (in nm).
    output_file (str): The file path where the YAML content will be saved.
    """
    system_Fn = 84.77  # System F-number
    pixel_size = 4.5  # Pixel size in microns
    wavelengths = list(range(initial_wavelength, final_wavelength + 1, wavelength_step))  # Convert to list
    nd_array = np.array(wavelengths) * system_Fn / 1000 / pixel_size  # Calculate the ND array

    # Open file for writing
    with open(output_file, "w") as f:
        f.write("---\n\n")

        # Main section
        f.write("""
main:
  root_dir:          '.\\calib'
  pixel_pupil:       80
  pixel_pitch:       1e-04
  total_time:        2401.0
  time_step:         1.0
  display_server:    false

pupilstop:
  class: 'Pupilstop'
  input_mask_data: 'mask80_g0125_0deg'
  
ramp:
  class: 'FuncGenerator'
  func_type: 'LINEAR'
  slope: [5]
  constant: [-6000]
                
on_axis_source:
  class:             'Source'
  polar_coordinate:  [0.0, 0.0]
  magnitude:         8
  wavelengthInNm:    500

prop:
  class: 'AtmoPropagation'
  source_dict_ref: ['on_axis_source']
  inputs:
    layer_list: ['pupilstop', 'dm.out_layer']
  outputs: ['out_on_axis_source_ef']

ifunc:
  class: 'IFunc'
  ifunc_data: 'ifunc_piston_80'
  mask_data: 'mask_piston_80'

dm:
  class: 'DM'
  ifunc_ref: 'ifunc'
  height: 0
  inputs:
      in_command: 'ramp.output'
  outputs:  ['out_layer']
""")

        # PSF instances for each wavelength
        f.write("\n")
        for idx, wl in enumerate(wavelengths):
            f.write(f"psf{wl}:\n")
            f.write(f"  class: 'PSF'\n")
            f.write(f"  wavelengthInNm: {wl}\n")
            f.write(f"  nd: {nd_array[idx]:.6f}\n")  
            f.write(f"  start_time: 0.\n")
            f.write(f"  inputs:\n")
            f.write(f"      in_ef: 'prop.out_on_axis_source_ef'\n")
            f.write(f"  outputs: ['out_psf']\n")
            f.write("\n")

        # Data store section
        f.write("\ndata_store:\n")
        f.write("  class: 'DataStore'\n")
        f.write("  store_dir: 'G:/Shared drives/PNRR-OAA/STILES/WP5000/Integration/SPL/Specula'\n")  
        f.write("  inputs:\n")
        f.write("    input_list: [\n")
        for wl in wavelengths:
            f.write(f"      'psf{wl}-psf{wl}.out_psf',\n")  
        #f.write("      'res_ef-prop.out_on_axis_source_ef'\n")
        f.write("    ]\n")

    print(f"YAML file '{output_file}' generated successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a YAML file for PSF calculations with a range of wavelengths.")
    parser.add_argument('initial_wavelength', type=int, help="The starting wavelength (in nm).")
    parser.add_argument('final_wavelength', type=int, help="The final wavelength (in nm).")
    parser.add_argument('wavelength_step', type=int, help="The step size for wavelength increments (in nm).")
    parser.add_argument('--output_file', type=str, default='params_spl_multiwave.yml', help="The output YAML file name (default is 'params_spl_multiwave.yml').")

    args = parser.parse_args()

    generateMultiwaveYml(args.initial_wavelength, args.final_wavelength, args.wavelength_step, args.output_file)
