"""
Utility functions for the SPL GUI.
"""

import tkinter as tk
from tkinter import filedialog
import os


def browse_folder(initial_dir=None):
    """Open a folder browser dialog."""
    folder = filedialog.askdirectory(initialdir=initial_dir or os.getcwd())
    return folder if folder else None


def browse_file(initial_dir=None, filetypes=None):
    """Open a file browser dialog."""
    if filetypes is None:
        filetypes = [("All files", "*.*")]
    
    file_path = filedialog.askopenfilename(
        initialdir=initial_dir or os.getcwd(),
        filetypes=filetypes
    )
    return file_path if file_path else None


def validate_float(value, min_val=None, max_val=None):
    """Validate a float value."""
    try:
        float_val = float(value)
        if min_val is not None and float_val < min_val:
            return False, f"Value must be >= {min_val}"
        if max_val is not None and float_val > max_val:
            return False, f"Value must be <= {max_val}"
        return True, float_val
    except ValueError:
        return False, "Invalid number"


def validate_int(value, min_val=None, max_val=None):
    """Validate an integer value."""
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            return False, f"Value must be >= {min_val}"
        if max_val is not None and int_val > max_val:
            return False, f"Value must be <= {max_val}"
        return True, int_val
    except ValueError:
        return False, "Invalid integer"


def create_labeled_entry(parent, label_text, row, default_value="", width=20):
    """Create a label and entry widget pair."""
    label = tk.Label(parent, text=label_text)
    label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    
    entry = tk.Entry(parent, width=width)
    entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
    if default_value:
        entry.insert(0, str(default_value))
    
    return entry


def create_labeled_entry_with_browse(parent, label_text, row, browse_callback, 
                                     default_value="", width=20, file_type="folder"):
    """Create a label, entry, and browse button."""
    label = tk.Label(parent, text=label_text)
    label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    
    frame = tk.Frame(parent)
    frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
    frame.columnconfigure(0, weight=1)
    
    entry = tk.Entry(frame, width=width)
    entry.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 5))
    if default_value:
        entry.insert(0, str(default_value))
    
    browse_btn = tk.Button(frame, text="Browse...", command=browse_callback)
    browse_btn.grid(row=0, column=1)
    
    return entry, browse_btn

