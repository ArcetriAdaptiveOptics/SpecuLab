"""
Tab for creating DM influence function.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.utils import create_labeled_entry, validate_int


class IFuncTab:
    """Tab for creating the DM influence function."""
    
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.status_callback = None
        
        # Title
        title = tk.Label(self.frame, text="Create DM Influence Function (Optional)", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.frame, 
            text="Generate an influence function with the same sampling as the pupil.\n"
                 "This step is optional but recommended for accurate simulations.",
            wraplength=600,
            justify=tk.CENTER
        )
        instructions.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(self.frame)
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Pixel pupil
        self.pixel_pupil_entry = create_labeled_entry(
            input_frame, "Pixel Pupil:", 0, "80", width=30
        )
        
        # Filename
        self.filename_entry = create_labeled_entry(
            input_frame, "IF Filename (with .fits):", 1, "ifunc_piston_80.fits", width=30
        )
        
        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=20)
        
        self.create_button = tk.Button(
            button_frame, 
            text="Create IF Function", 
            command=self.create_ifunc,
            bg="#2196F3",
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
    
    def create_ifunc(self):
        """Create the influence function using create_dm_ifunc.py."""
        # Validate inputs
        valid, pixel_pupil = validate_int(self.pixel_pupil_entry.get(), min_val=1)
        if not valid:
            messagebox.showerror("Error", f"Invalid pixel pupil: {pixel_pupil}")
            return
        
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Error", "Filename cannot be empty")
            return
        
        # Ensure filename has .fits extension
        if not filename.endswith('.fits'):
            filename += '.fits'
        
        # Disable button during execution
        self.create_button.config(state=tk.DISABLED)
        self.update_status("Creating influence function...")
        
        # Run in separate thread to avoid blocking UI
        def run_create_ifunc():
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                
                from create_dm_ifunc import createDmInfluenceFunction
                
                step_response = createDmInfluenceFunction(size=pixel_pupil, filename=filename)
                
                # Save step response
                saved_file_path = step_response.save_step_response()
                
                # Save mask piston
                mask_piston_file_path = step_response.save_mask_piston()
                
                self.frame.after(0, lambda: self.update_status(
                    f"IF function created successfully!"
                ))
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Influence function created successfully!\n\n"
                    f"Step response: {saved_file_path}\n"
                    f"Mask piston: {mask_piston_file_path}"
                ))
            except Exception as e:
                error_msg = f"Error creating IF function: {str(e)}"
                self.frame.after(0, lambda: self.update_status(error_msg))
                self.frame.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.frame.after(0, lambda: self.create_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_create_ifunc, daemon=True)
        thread.start()

