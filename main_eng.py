#!/usr/bin/env python3
"""
System Audit Dashboard - Final Version (English)
---------------------------------------------------
A centralized dashboard for monitoring Linux systems, providing a real-time overview of key system information:
  - Kernel version
  - Operating System details
  - Logged-in user
  - Number of active processes
  - Number of open ports
  - Load average (1 min, 5 min, 15 min)
  - Available memory (in MB)
  - Disk usage (percentage used on /)

The dashboard features:
  - A bar chart (using Matplotlib) to visualize the load average.
  - A configurable update interval (in seconds) set by the user.
  - Data collection running in a separate thread to keep the GUI responsive.
  - Periodic updates via Tkinter's after() method.
  - Logging of all operations and errors to "sys_audit_dashboard.log".

Author: Bocaletto Luca
License: GPL
"""

import os
import subprocess
import platform
import getpass
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import logging

# Import Matplotlib for the graph
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    messagebox.showerror("Error", "Matplotlib is not installed. Please install it via pip and try again.")
    exit(1)

# Logging configuration
logging.basicConfig(
    filename="sys_audit_dashboard.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("System Audit Dashboard started.")

# Directories to exclude from scanning
EXCLUDE_DIRS = ["/proc", "/sys", "/dev"]

class SystemAuditDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Audit Dashboard")
        self.geometry("1000x750")
        self.configure(bg="white")
        # Tkinter variables for system information
        self.kernel_var = tk.StringVar(value="N/A")
        self.os_var = tk.StringVar(value="N/A")
        self.user_var = tk.StringVar(value="N/A")
        self.processes_var = tk.StringVar(value="N/A")
        self.ports_var = tk.StringVar(value="N/A")
        self.load_var = tk.StringVar(value="N/A")
        self.memory_var = tk.StringVar(value="N/A")
        self.disk_var = tk.StringVar(value="N/A")
        # Update interval configuration (in seconds)
        self.interval_sec = tk.IntVar(value=60)
        self.interval_ms = self.interval_sec.get() * 1000
        
        # Load average values (tuple: (1min, 5min, 15min))
        self.load_values = (0, 0, 0)
        
        self.create_widgets()
        # Start the dashboard update
        self.update_dashboard()

    def create_widgets(self):
        # Header
        header = ttk.Label(self, text="System Audit Dashboard", font=("Helvetica", 24, "bold"),
                           background="#343a40", foreground="white", anchor="center")
        header.pack(fill=tk.X)
        
        # Configuration frame for the update interval.
        config_frame = ttk.Frame(self)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        lbl_interval = ttk.Label(config_frame, text="Update Interval (sec):")
        lbl_interval.pack(side=tk.LEFT, padx=5)
        self.entry_interval = ttk.Entry(config_frame, textvariable=self.interval_sec, width=5)
        self.entry_interval.pack(side=tk.LEFT, padx=5)
        btn_set_interval = ttk.Button(config_frame, text="Set", command=self.set_interval)
        btn_set_interval.pack(side=tk.LEFT, padx=5)
        
        # Frame for system information
        info_frame = ttk.Frame(self)
        info_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Column 1: Kernel, OS and User
        lbl_kernel = ttk.Label(info_frame, text="Kernel Version:")
        lbl_kernel.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.val_kernel = ttk.Label(info_frame, textvariable=self.kernel_var)
        self.val_kernel.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        lbl_os = ttk.Label(info_frame, text="OS:")
        lbl_os.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.val_os = ttk.Label(info_frame, textvariable=self.os_var)
        self.val_os.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        lbl_user = ttk.Label(info_frame, text="Logged-in User:")
        lbl_user.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.val_user = ttk.Label(info_frame, textvariable=self.user_var)
        self.val_user.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Column 2: Processes, Open Ports, and Load Average
        lbl_processes = ttk.Label(info_frame, text="Number of Processes:")
        lbl_processes.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.val_processes = ttk.Label(info_frame, textvariable=self.processes_var)
        self.val_processes.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        lbl_ports = ttk.Label(info_frame, text="Open Ports:")
        lbl_ports.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.val_ports = ttk.Label(info_frame, textvariable=self.ports_var)
        self.val_ports.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        lbl_load = ttk.Label(info_frame, text="Load Average (1m/5m/15m):")
        lbl_load.grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.val_load = ttk.Label(info_frame, textvariable=self.load_var)
        self.val_load.grid(row=2, column=3, sticky="w", padx=5, pady=5)
        
        # Additional metrics: Memory and Disk Usage
        lbl_memory = ttk.Label(info_frame, text="Available Memory:")
        lbl_memory.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.val_memory = ttk.Label(info_frame, textvariable=self.memory_var)
        self.val_memory.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        lbl_disk = ttk.Label(info_frame, text="Disk Usage (/):")
        lbl_disk.grid(row=3, column=2, sticky="w", padx=5, pady=5)
        self.val_disk = ttk.Label(info_frame, textvariable=self.disk_var)
        self.val_disk.grid(row=3, column=3, sticky="w", padx=5, pady=5)
        
        # Manual update button
        btn_refresh = ttk.Button(self, text="Manual Update", command=self.update_dashboard)
        btn_refresh.pack(pady=5)
        
        # Graph frame for Load Average
        graph_frame = ttk.LabelFrame(self, text="Load Average Graph")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the Matplotlib figure
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Load Average")
        self.ax.set_ylim(0, 5)
        self.ax.set_xticks([0, 1, 2])
        self.ax.set_xticklabels(["1 min", "5 min", "15 min"])
        self.bars = self.ax.bar([0, 1, 2], [0, 0, 0], color="skyblue")
        
        # Embed the figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Output text area for log/info messages
        self.text_output = ScrolledText(self, wrap=tk.WORD, height=8)
        self.text_output.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.text_output.insert(tk.END, "Initializing dashboard...\n")
        
    def set_interval(self):
        """
        Update the update interval from the entry field.
        """
        try:
            sec = int(self.entry_interval.get())
            self.interval_sec.set(sec)
            self.interval_ms = sec * 1000
            self.text_output.insert(tk.END, f"Update interval set to {sec} seconds.\n")
        except Exception as e:
            messagebox.showerror("Error", "Please enter a valid numeric value for the interval.")
    
    def thread_update(self):
        """
        Function executed in a separate thread to gather system data.
        """
        data = {}
        try:
            data["kernel"] = subprocess.check_output("uname -r", shell=True, universal_newlines=True).strip()
        except Exception as e:
            data["kernel"] = "Error"
            logger.error(f"Error retrieving kernel: {e}")
        try:
            data["os"] = platform.platform()
        except Exception as e:
            data["os"] = "Error"
            logger.error(f"Error retrieving OS info: {e}")
        try:
            data["user"] = getpass.getuser()
        except Exception as e:
            data["user"] = "Error"
            logger.error(f"Error retrieving user: {e}")
        try:
            ps_output = subprocess.check_output("ps aux", shell=True, universal_newlines=True)
            data["processes"] = len(ps_output.splitlines()) - 1
        except Exception as e:
            data["processes"] = "Error"
            logger.error(f"Error retrieving processes: {e}")
        try:
            try:
                ports_output = subprocess.check_output("netstat -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            except Exception:
                ports_output = subprocess.check_output("ss -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            port_lines = ports_output.splitlines()[2:]
            data["ports"] = len(port_lines)
        except Exception as e:
            data["ports"] = "Error"
            logger.error(f"Error retrieving open ports: {e}")
        try:
            data["load"] = os.getloadavg()
        except Exception as e:
            data["load"] = (0, 0, 0)
            logger.error(f"Error retrieving load average: {e}")
        try:
            free_output = subprocess.check_output("free -m", shell=True, universal_newlines=True)
            for line in free_output.splitlines():
                if line.startswith("Mem:"):
                    parts = line.split()
                    data["memory"] = parts[6] + " MB"
                    break
        except Exception as e:
            data["memory"] = "Error"
            logger.error(f"Error retrieving memory info: {e}")
        try:
            df_output = subprocess.check_output("df -h /", shell=True, universal_newlines=True)
            lines = df_output.splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                data["disk"] = parts[4]
            else:
                data["disk"] = "N/A"
        except Exception as e:
            data["disk"] = "Error"
            logger.error(f"Error retrieving disk usage: {e}")
        return data

    def update_gui(self, data):
        """
        Updates the Tkinter variables and the graph with the collected data.
        """
        self.kernel_var.set(data.get("kernel", "N/A"))
        self.os_var.set(data.get("os", "N/A"))
        self.user_var.set(data.get("user", "N/A"))
        self.processes_var.set(data.get("processes", "N/A"))
        self.ports_var.set(data.get("ports", "N/A"))
        load = data.get("load", (0, 0, 0))
        self.load_values = load
        self.load_var.set(f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}")
        self.memory_var.set(data.get("memory", "N/A"))
        self.disk_var.set(data.get("disk", "N/A"))
        self.update_graph()
        now = time.strftime("%H:%M:%S")
        self.text_output.insert(tk.END, f"Dashboard updated at {now}.\n")
        self.lbl_status.config(text="Dashboard updated.")

    def thread_update_wrapper(self):
        """
        Wrapper function executed within a thread to update the GUI in a thread-safe way.
        """
        data = self.thread_update()
        self.after(0, lambda: self.update_gui(data))
    
    def update_dashboard(self):
        """
        Starts a thread to update the dashboard and schedules the next update based on the configured interval.
        """
        threading.Thread(target=self.thread_update_wrapper, daemon=True).start()
        self.after(self.interval_ms, self.update_dashboard)
    
    def update_graph(self):
        """
        Updates the bar chart with the current load average values.
        """
        try:
            values = list(self.load_values)
            for bar, val in zip(self.bars, values):
                bar.set_height(val)
            max_val = max(values) if values else 5
            self.ax.set_ylim(0, max(max_val * 1.2, 5))
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Error updating graph: {e}")

if __name__ == "__main__":
    app = SystemAuditDashboard()
    app.mainloop()
