"""
Tab for creating SPL mask.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.utils import create_labeled_entry, validate_int, validate_float


class MaskTab:
    """Tab for creating the SPL mask."""
    
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.status_callback = None
        
        # Title
        title = tk.Label(self.frame, text="Create SPL Mask", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.frame, 
            text="Generate a circular mask with an optional gap for SPL calibration.",
            wraplength=600
        )
        instructions.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(self.frame)
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Pixel pupil
        self.pixel_pupil_entry = create_labeled_entry(
            input_frame, "Pixel Pupil:", 0, "80", width=30
        )
        
        # Gap fraction
        self.gap_entry = create_labeled_entry(
            input_frame, "Gap Fraction:", 1, "0.0", width=30
        )
        
        # Clock angle
        self.clock_angle_entry = create_labeled_entry(
            input_frame, "Clock Angle (degrees):", 2, "0.0", width=30
        )
        
        # Filename
        self.filename_entry = create_labeled_entry(
            input_frame, "Filename (without .fits):", 3, "mymask", width=30
        )
        
        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=20)
        
        self.create_button = tk.Button(
            button_frame, 
            text="Create Mask", 
            command=self.create_mask,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10
        )
        self.create_button.pack()
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", fg="blue")
        self.status_label.pack(pady=10)
    
    def set_status_callback(self, callback):
        """Set the status callback function."""
        self.status_callback = callback
    
    def update_status(self, message):
        """Update status message."""
        if self.status_callback:
            self.status_callback(message)
        self.status_label.config(text=message)
    
    def create_mask(self):
        """Create the mask using the create_spl_mask.py script."""
        # Validate inputs
        valid, pixel_pupil = validate_int(self.pixel_pupil_entry.get(), min_val=1)
        if not valid:
            messagebox.showerror("Error", f"Invalid pixel pupil: {pixel_pupil}")
            return
        
        valid, gap = validate_float(self.gap_entry.get(), min_val=0.0)
        if not valid:
            messagebox.showerror("Error", f"Invalid gap fraction: {gap}")
            return
        
        valid, clock_angle = validate_float(self.clock_angle_entry.get())
        if not valid:
            messagebox.showerror("Error", f"Invalid clock angle: {clock_angle}")
            return
        
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Filename cannot be empty")
            return
        
        # Disable button during execution
        self.create_button.config(state=tk.DISABLED)
        self.update_status("Creating mask...")
        
        # Run in separate thread to avoid blocking UI
        def run_create_mask():
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                
                from create_spl_mask import createSplMask
                
                # Ensure filename doesn't have .fits extension (script adds it)
                if filename.endswith('.fits'):
                    clean_filename = filename[:-5]
                else:
                    clean_filename = filename
                
                createSplMask(
                    pixel_pupil=pixel_pupil,
                    gap=gap,
                    clock_angle=clock_angle,
                    filename=clean_filename
                )
                
                self.frame.after(0, lambda: self.update_status(
                    f"Mask created successfully: {clean_filename}.fits"
                ))
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Mask created successfully!\nSaved as: {clean_filename}.fits\nLocation: .\\calib\\data\\"
                ))
            except Exception as e:
                error_msg = f"Error creating mask: {str(e)}"
                self.frame.after(0, lambda: self.update_status(error_msg))
                self.frame.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.frame.after(0, lambda: self.create_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_create_mask, daemon=True)
        thread.start()

