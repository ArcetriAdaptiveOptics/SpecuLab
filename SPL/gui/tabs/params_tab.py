"""
Tab for setting piston scan parameters and generating YAML file.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.utils import create_labeled_entry, validate_int, validate_float


class ParamsTab:
    """Tab for setting parameters and generating YAML file."""
    
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.status_callback = None
        
        # Create scrollable frame
        canvas = tk.Canvas(self.frame)
        scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title = tk.Label(scrollable_frame, text="Set Piston Scan Parameters", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            scrollable_frame, 
            text="Configure parameters for the PSF simulation and generate the YAML file.",
            wraplength=600
        )
        instructions.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(scrollable_frame)
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Wavelength parameters
        tk.Label(input_frame, text="Wavelength Parameters", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.initial_wavelength_entry = create_labeled_entry(
            input_frame, "Initial Wavelength (nm):", row, "520", width=30
        )
        row += 1
        
        self.final_wavelength_entry = create_labeled_entry(
            input_frame, "Final Wavelength (nm):", row, "539", width=30
        )
        row += 1
        
        self.wavelength_step_entry = create_labeled_entry(
            input_frame, "Wavelength Step (nm):", row, "5", width=30
        )
        row += 1
        
        # Main parameters
        tk.Label(input_frame, text="Main Parameters", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.pixel_pupil_entry = create_labeled_entry(
            input_frame, "Pixel Pupil:", row, "80", width=30
        )
        row += 1
        
        self.pixel_pitch_entry = create_labeled_entry(
            input_frame, "Pixel Pitch (m):", row, "8.375e-05", width=30
        )
        row += 1
        
        self.total_time_entry = create_labeled_entry(
            input_frame, "Total Time (iterations):", row, "2401.0", width=30
        )
        row += 1
        
        self.time_step_entry = create_labeled_entry(
            input_frame, "Time Step:", row, "1.0", width=30
        )
        row += 1
        
        # Mask parameters
        tk.Label(input_frame, text="Mask Parameters", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.mask_data_entry = create_labeled_entry(
            input_frame, "Input Mask Data (name w/o .fits):", row, "mask_g0150_0deg", width=30
        )
        row += 1
        
        # Ramp parameters
        tk.Label(input_frame, text="Ramp Parameters (WF Piston)", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.ramp_slope_entry = create_labeled_entry(
            input_frame, "Ramp Slope (nm/step):", row, "10", width=30
        )
        row += 1
        
        self.ramp_constant_entry = create_labeled_entry(
            input_frame, "Ramp Constant (nm):", row, "-12000", width=30
        )
        row += 1
        
        # IF parameters
        tk.Label(input_frame, text="Influence Function Parameters", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.ifunc_data_entry = create_labeled_entry(
            input_frame, "IF Data (name w/o .fits):", row, "ifunc_piston_80", width=30
        )
        row += 1
        
        self.mask_piston_entry = create_labeled_entry(
            input_frame, "Mask Piston (name w/o .fits):", row, "mask_piston_80", width=30
        )
        row += 1
        
        # Store directory
        tk.Label(input_frame, text="Data Storage", 
                font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.store_dir_entry = create_labeled_entry(
            input_frame, "Store Directory:", row, "D:/Data/SPL_Data", width=30
        )
        row += 1
        
        # Output filename
        self.output_file_entry = create_labeled_entry(
            input_frame, "Output YAML File:", row, "params_spl_multiwave.yml", width=30
        )
        row += 1
        
        # Button frame
        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        
        self.generate_button = tk.Button(
            button_frame, 
            text="Generate YAML File", 
            command=self.generate_yml,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10
        )
        self.generate_button.pack()
        
        # Status label
        self.status_label = tk.Label(scrollable_frame, text="", fg="blue")
        self.status_label.pack(pady=10)
    
    def set_status_callback(self, callback):
        """Set the status callback function."""
        self.status_callback = callback
    
    def update_status(self, message):
        """Update status message."""
        if self.status_callback:
            self.status_callback(message)
        self.status_label.config(text=message)
    
    def generate_yml(self):
        """Generate the YAML file using generate_multiwave_yml.py."""
        # Validate inputs
        valid, initial_wl = validate_int(self.initial_wavelength_entry.get(), min_val=1)
        if not valid:
            messagebox.showerror("Error", f"Invalid initial wavelength: {initial_wl}")
            return
        
        valid, final_wl = validate_int(self.final_wavelength_entry.get(), min_val=initial_wl)
        if not valid:
            messagebox.showerror("Error", f"Invalid final wavelength: {final_wl}")
            return
        
        valid, wl_step = validate_int(self.wavelength_step_entry.get(), min_val=1)
        if not valid:
            messagebox.showerror("Error", f"Invalid wavelength step: {wl_step}")
            return
        
        output_file = self.output_file_entry.get().strip()
        if not output_file:
            messagebox.showerror("Error", "Output filename cannot be empty")
            return
        
        # Disable button during execution
        self.generate_button.config(state=tk.DISABLED)
        self.update_status("Generating YAML file...")
        
        # Run in separate thread
        def run_generate_yml():
            try:
                from generate_multiwave_yml import generateMultiwaveYml
                import yaml
                import re
                
                # Generate basic YAML
                generateMultiwaveYml(initial_wl, final_wl, wl_step, output_file)
                
                # Read the generated YAML file
                with open(output_file, 'r') as f:
                    yaml_content = f.read()
                
                # Replace parameters using regex (since the file is written as text)
                yaml_content = re.sub(
                    r"pixel_pupil:\s*\d+",
                    f"pixel_pupil:       {int(self.pixel_pupil_entry.get())}",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"pixel_pitch:\s*[\d.e-]+",
                    f"pixel_pitch:       {self.pixel_pitch_entry.get()}",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"total_time:\s*[\d.]+",
                    f"total_time:        {float(self.total_time_entry.get())}",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"time_step:\s*[\d.]+",
                    f"time_step:         {float(self.time_step_entry.get())}",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"input_mask_data:\s*'[^']+'",
                    f"input_mask_data: '{self.mask_data_entry.get().strip()}'",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"slope:\s*\[[\d.]+\]",
                    f"slope: [{float(self.ramp_slope_entry.get())}]",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"constant:\s*\[[\d-]+\]",
                    f"constant: [{float(self.ramp_constant_entry.get())}]",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"ifunc_data:\s*'[^']+'",
                    f"ifunc_data: '{self.ifunc_data_entry.get().strip()}'",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"mask_data:\s*'[^']+'",
                    f"mask_data: '{self.mask_piston_entry.get().strip()}'",
                    yaml_content
                )
                yaml_content = re.sub(
                    r"store_dir:\s*'[^']+'",
                    f"store_dir: '{self.store_dir_entry.get().strip()}'",
                    yaml_content
                )
                
                # Write back
                with open(output_file, 'w') as f:
                    f.write(yaml_content)
                
                self.frame.after(0, lambda: self.update_status(
                    f"YAML file generated successfully: {output_file}"
                ))
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"YAML file generated successfully!\n\nSaved as: {output_file}"
                ))
            except Exception as e:
                error_msg = f"Error generating YAML file: {str(e)}"
                self.frame.after(0, lambda: self.update_status(error_msg))
                self.frame.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.frame.after(0, lambda: self.generate_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_generate_yml, daemon=True)
        thread.start()

