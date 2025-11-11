"""
Tab for running the PSF simulation.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os
import threading
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.utils import create_labeled_entry_with_browse, browse_file


class SimulationTab:
    """Tab for running the simulation."""
    
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.status_callback = None
        self.process = None
        
        # Title
        title = tk.Label(self.frame, text="Run PSF Simulation", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.frame, 
            text="Run the SPECULA simulation using the generated YAML parameter file.",
            wraplength=600
        )
        instructions.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(self.frame)
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # YAML file selection
        self.yml_file_entry, self.browse_btn = create_labeled_entry_with_browse(
            input_frame,
            "YAML Parameter File:",
            0,
            self.browse_yml_file,
            "params_spl_multiwave.yml",
            width=40,
            file_type="file"
        )
        
        # Options frame
        options_frame = tk.Frame(input_frame)
        options_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        self.use_cpu_var = tk.BooleanVar()
        cpu_check = tk.Checkbutton(
            options_frame, 
            text="Use CPU (instead of GPU)", 
            variable=self.use_cpu_var
        )
        cpu_check.pack(anchor=tk.W)
        
        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=20)
        
        self.run_button = tk.Button(
            button_frame, 
            text="Run Simulation", 
            command=self.run_simulation,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            button_frame, 
            text="Stop Simulation", 
            command=self.stop_simulation,
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Output text area
        output_label = tk.Label(self.frame, text="Simulation Output:", font=("Arial", 10, "bold"))
        output_label.pack(pady=(20, 5))
        
        output_frame = tk.Frame(self.frame)
        output_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(output_frame, height=10, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
    
    def browse_yml_file(self):
        """Browse for YAML file."""
        file_path = browse_file(
            filetypes=[("YAML files", "*.yml"), ("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if file_path:
            self.yml_file_entry.delete(0, tk.END)
            self.yml_file_entry.insert(0, file_path)
    
    def run_simulation(self):
        """Run the simulation using main_simul.py."""
        yml_file = self.yml_file_entry.get().strip()
        if not yml_file:
            messagebox.showerror("Error", "Please select a YAML parameter file")
            return
        
        if not os.path.exists(yml_file):
            messagebox.showerror("Error", f"YAML file not found: {yml_file}")
            return
        
        # Disable run button, enable stop button
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.update_status("Running simulation...")
        
        # Run in separate thread
        def run_sim():
            try:
                # Build command
                cmd = [sys.executable, "main_simul.py", yml_file]
                if self.use_cpu_var.get():
                    cmd.append("--cpu")
                
                # Change to SPL directory
                spl_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                os.chdir(spl_dir)
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Read output line by line
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.frame.after(0, lambda l=line: self.output_text.insert(tk.END, l))
                        self.frame.after(0, lambda: self.output_text.see(tk.END))
                
                self.process.wait()
                
                if self.process.returncode == 0:
                    self.frame.after(0, lambda: self.update_status("Simulation completed successfully!"))
                    self.frame.after(0, lambda: messagebox.showinfo("Success", "Simulation completed successfully!"))
                else:
                    self.frame.after(0, lambda: self.update_status(f"Simulation ended with code {self.process.returncode}"))
                    self.frame.after(0, lambda: messagebox.showwarning("Warning", f"Simulation ended with code {self.process.returncode}"))
            except Exception as e:
                error_msg = f"Error running simulation: {str(e)}"
                self.frame.after(0, lambda: self.update_status(error_msg))
                self.frame.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.frame.after(0, lambda: self.run_button.config(state=tk.NORMAL))
                self.frame.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
                self.process = None
        
        thread = threading.Thread(target=run_sim, daemon=True)
        thread.start()
    
    def stop_simulation(self):
        """Stop the running simulation."""
        if self.process:
            try:
                self.process.terminate()
                self.update_status("Stopping simulation...")
            except Exception as e:
                messagebox.showerror("Error", f"Error stopping simulation: {str(e)}")

