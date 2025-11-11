"""
Launcher script for the SPL GUI application.
Run this script to start the graphical user interface.
"""

import sys
import os

# Add the SPL directory to the path
spl_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, spl_dir)

# Change to SPL directory
os.chdir(spl_dir)

# Import and run the GUI
from gui.main import main

if __name__ == "__main__":
    main()

