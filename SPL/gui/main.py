"""
Main GUI application for SPL calibration workflow.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path to import SPL modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.tabs.mask_tab import MaskTab
from gui.tabs.ifunc_tab import IFuncTab
from gui.tabs.params_tab import ParamsTab
from gui.tabs.simulation_tab import SimulationTab
from gui.tabs.fringes_tab import FringesTab


class SPLGUI:
    """Main application window for SPL calibration workflow."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SPL Calibration Workflow")
        self.root.geometry("900x700")
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.mask_tab = MaskTab(self.notebook)
        self.ifunc_tab = IFuncTab(self.notebook)
        self.params_tab = ParamsTab(self.notebook)
        self.simulation_tab = SimulationTab(self.notebook)
        self.fringes_tab = FringesTab(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.mask_tab.frame, text="1. Create Mask")
        self.notebook.add(self.ifunc_tab.frame, text="2. Create IF Func (Optional)")
        self.notebook.add(self.params_tab.frame, text="3. Set Parameters")
        self.notebook.add(self.simulation_tab.frame, text="4. Run Simulation")
        self.notebook.add(self.fringes_tab.frame, text="5. Create Fringes")
        
        # Add status bar
        self.status_bar = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set status method for tabs
        for tab in [self.mask_tab, self.ifunc_tab, self.params_tab, 
                   self.simulation_tab, self.fringes_tab]:
            tab.set_status_callback(self.update_status)
    
    def update_status(self, message):
        """Update the status bar message."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = SPLGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

