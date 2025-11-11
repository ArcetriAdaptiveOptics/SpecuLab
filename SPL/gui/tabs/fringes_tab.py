"""
Tab for creating fringe patterns from PSF files.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.utils import (
    create_labeled_entry, 
    create_labeled_entry_with_browse,
    browse_folder,
    validate_float,
    validate_int
)


class FringesTab:
    """Tab for creating fringe patterns."""
    
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
        title = tk.Label(scrollable_frame, text="Create Fringe Patterns", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            scrollable_frame, 
            text="Extract fringe patterns from simulated PSF files.\n"
                 "The script will auto-detect piston values from FITS files if not specified.",
            wraplength=600,
            justify=tk.CENTER
        )
        instructions.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(scrollable_frame)
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Parent folder
        def browse_parent_folder():
            folder = browse_folder()
            if folder:
                self.parent_folder_entry.delete(0, tk.END)
                self.parent_folder_entry.insert(0, folder)
        
        self.parent_folder_entry, _ = create_labeled_entry_with_browse(
            input_frame,
            "Parent Folder (with PSF files):",
            row,
            browse_parent_folder,
            "",
            width=40,
            file_type="folder"
        )
        row += 1
        
        # Output folder
        def browse_output_folder():
            folder = browse_folder()
            if folder:
                self.output_folder_entry.delete(0, tk.END)
                self.output_folder_entry.insert(0, folder)
        
        self.output_folder_entry, _ = create_labeled_entry_with_browse(
            input_frame,
            "Output Folder:",
            row,
            browse_output_folder,
            "Fringes",
            width=40,
            file_type="folder"
        )
        row += 1
        
        # Number of rows
        self.num_rows_entry = create_labeled_entry(
            input_frame, "Number of Rows to Accumulate:", row, "1", width=30
        )
        row += 1
        
        # Piston parameters (optional)
        tk.Label(input_frame, text="Piston Parameters (Optional - auto-detected if not specified)", 
                font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, 
                sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.piston_min_entry = create_labeled_entry(
            input_frame, "Piston Min (nm):", row, "", width=30
        )
        row += 1
        
        self.piston_max_entry = create_labeled_entry(
            input_frame, "Piston Max (nm):", row, "", width=30
        )
        row += 1
        
        self.piston_step_entry = create_labeled_entry(
            input_frame, "Piston Step (nm):", row, "", width=30
        )
        row += 1
        
        # Piston file (optional)
        def browse_piston_file():
            from gui.utils import browse_file
            file_path = browse_file(
                filetypes=[("FITS files", "*.fits"), ("All files", "*.*")]
            )
            if file_path:
                self.piston_file_entry.delete(0, tk.END)
                self.piston_file_entry.insert(0, file_path)
        
        self.piston_file_entry, _ = create_labeled_entry_with_browse(
            input_frame,
            "Piston File (optional, overrides other piston params):",
            row,
            browse_piston_file,
            "",
            width=40,
            file_type="file"
        )
        row += 1
        
        # Button frame
        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        
        self.create_button = tk.Button(
            button_frame, 
            text="Create Fringes", 
            command=self.create_fringes,
            bg="#E91E63",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10
        )
        self.create_button.pack()
        
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
    
    def create_fringes(self):
        """Create fringe patterns using create_fringes.py."""
        # Validate inputs
        parent_folder = self.parent_folder_entry.get().strip()
        if not parent_folder:
            messagebox.showerror("Error", "Parent folder cannot be empty")
            return
        
        if not os.path.exists(parent_folder):
            messagebox.showerror("Error", f"Parent folder not found: {parent_folder}")
            return
        
        output_folder = self.output_folder_entry.get().strip()
        if not output_folder:
            output_folder = "Fringes"
        
        # Validate optional parameters
        num_rows = 1
        if self.num_rows_entry.get().strip():
            valid, num_rows = validate_int(self.num_rows_entry.get(), min_val=1)
            if not valid:
                messagebox.showerror("Error", f"Invalid number of rows: {num_rows}")
                return
        
        piston_min = None
        if self.piston_min_entry.get().strip():
            valid, piston_min = validate_float(self.piston_min_entry.get())
            if not valid:
                messagebox.showerror("Error", f"Invalid piston min: {piston_min}")
                return
        
        piston_max = None
        if self.piston_max_entry.get().strip():
            valid, piston_max = validate_float(self.piston_max_entry.get())
            if not valid:
                messagebox.showerror("Error", f"Invalid piston max: {piston_max}")
                return
        
        piston_step = None
        if self.piston_step_entry.get().strip():
            valid, piston_step = validate_float(self.piston_step_entry.get())
            if not valid:
                messagebox.showerror("Error", f"Invalid piston step: {piston_step}")
                return
        
        piston_file = self.piston_file_entry.get().strip() or None
        if piston_file and not os.path.exists(piston_file):
            messagebox.showerror("Error", f"Piston file not found: {piston_file}")
            return
        
        # Disable button during execution
        self.create_button.config(state=tk.DISABLED)
        self.update_status("Creating fringe patterns...")
        
        # Run in separate thread
        def run_create_fringes():
            try:
                from create_fringes import process_all_piston_values
                import numpy as np
                from astropy.io import fits
                
                # Read piston values from file if provided
                piston_values = None
                if piston_file:
                    with fits.open(piston_file) as hdul:
                        piston_values = hdul[0].data
                
                process_all_piston_values(
                    parent_folder=parent_folder,
                    output_folder=output_folder,
                    num_rows_to_accumulate=num_rows,
                    piston_min=piston_min,
                    piston_max=piston_max,
                    piston_step=piston_step,
                    piston_values=piston_values
                )
                
                self.frame.after(0, lambda: self.update_status(
                    f"Fringe patterns created successfully in: {output_folder}"
                ))
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Fringe patterns created successfully!\n\n"
                    f"Output folder: {output_folder}"
                ))
            except Exception as e:
                error_msg = f"Error creating fringes: {str(e)}"
                self.frame.after(0, lambda: self.update_status(error_msg))
                self.frame.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.frame.after(0, lambda: self.create_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_create_fringes, daemon=True)
        thread.start()

