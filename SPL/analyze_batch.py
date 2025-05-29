import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from fringes_matching import main as fringes_matching_main
import argparse
from pathlib import Path

def extract_tt_number(folder_path):
    """Extract TT number from folder path."""
    match = re.search(r'(\d+)_\d+$', folder_path)
    if match:
        return int(match.group(1))
    return None

def process_tt_folder(tt_folder, pos_id, pattern="*.fits"):
    """Process a single TT folder and return the TT number and piston value."""
    # Construct the specific filename for this position
    target_filename = f'fringe_result_pos{pos_id}.fits'
    target_file = os.path.join(tt_folder, target_filename)
    
    if not os.path.exists(target_file):
        print(f"Target file not found: {target_file}")
        return None, None
    
    # Create a temporary argument parser to pass the target file to fringes_matching
    class Args:
        def __init__(self, target_fits_path):
            self.target_fits_path = target_fits_path
    
    # Run fringes_matching on the target file
    args = Args(target_file)
    
    try:
        # Call fringes_matching_main and get piston_value directly
        piston_value = fringes_matching_main(args)
        
        # Extract TT number from the folder name
        tt_number = extract_tt_number(tt_folder)
        if tt_number is None:
            print(f"Could not extract TT number from {tt_folder}")
            return None, None
        
        return tt_number, piston_value
        
    except Exception as e:
        print(f"Error processing {tt_folder}: {e}")
        return None, None

def plot_piston_values(tt_numbers, piston_values, output_dir, pos_id):
    """Plot differential piston values as a function of TT number."""
    plt.figure(figsize=(12, 6))
    plt.plot(tt_numbers, piston_values, 'bo-', label='Differential Piston')
    plt.xlabel('TT Number')
    plt.ylabel('Differential Piston (nm)')
    plt.title(f'Differential Piston Values vs TT Number (Position {pos_id})')
    plt.grid(True)
    plt.legend()
    
    # Save the plot
    output_path = os.path.join(output_dir, f'piston_values_pos{pos_id}_plot.png')
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Process multiple TT folders and plot differential piston values.")
    parser.add_argument("base_dir", help="Base directory containing TT folders")
    parser.add_argument("--pattern", default="20250508_*", help="Pattern to match TT folders")
    parser.add_argument("--pos-id", required=True, help="Position ID to process (e.g., '001' for fringe_result_001.fits)")
    args = parser.parse_args()
    
    # Find all matching TT folders
    tt_folders = glob.glob(os.path.join(args.base_dir, args.pattern))
    if not tt_folders:
        print(f"No folders found matching pattern {args.pattern} in {args.base_dir}")
        return
    
    # Process each TT folder
    tt_numbers = []
    piston_values = []
    
    for tt_folder in sorted(tt_folders):
        print(f"\nProcessing folder: {tt_folder}")
        tt_number, piston_value = process_tt_folder(tt_folder, args.pos_id)
        if tt_number is not None and piston_value is not None:
            tt_numbers.append(tt_number)
            piston_values.append(piston_value)
            print(f"TT {tt_number}: Piston value = {piston_value:.2f} nm")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(args.base_dir, "analysis_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot the results
    if tt_numbers and piston_values:
        plot_piston_values(tt_numbers, piston_values, output_dir, args.pos_id)
        
        # Save the data to a text file
        data_path = os.path.join(output_dir, f'piston_values_pos{args.pos_id}.txt')
        with open(data_path, 'w') as f:
            f.write("TT_Number,Piston_Value(nm)\n")
            for tt, piston in zip(tt_numbers, piston_values):
                f.write(f"{tt},{piston:.2f}\n")
        print(f"Data saved to {data_path}")
    else:
        print("No valid data to plot")

if __name__ == "__main__":
    main()
