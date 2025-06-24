#!/usr/bin/env python3
"""
System Audit Dashboard - Final Release
-----------------------------------------
A Linux system monitoring dashboard that provides a real-time overview of key system information,
including:
  - Kernel version
  - Operating System details
  - Logged-in user
  - Number of running processes
  - Number of open ports
  - Load Average (1, 5, 15 minutes)
  
The dashboard also displays a bar chart of the current load average values.
The information is updated periodically (every 60 seconds) and can be refreshed manually.

Author: [Il Tuo Nome]
License: GPL
"""

import os
import subprocess
import platform
import getpass
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import logging
import time

# Import di Matplotlib per il grafico
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    messagebox.showerror("Errore", "Il modulo matplotlib non è installato. Installalo tramite pip e riprova.")
    exit(1)

# Configurazione del logging
logging.basicConfig(
    filename="sys_audit_dashboard.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("System Audit Dashboard avviato.")

# Costante per l'aggiornamento periodico (in millisecondi)
UPDATE_INTERVAL_MS = 60000  # 60 secondi

class SystemAuditDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Audit Dashboard")
        self.geometry("1000x700")
        self.configure(bg="white")
        
        # Inizializzazione delle variabili di sistema
        self.kernel_version = tk.StringVar(value="N/D")
        self.os_info = tk.StringVar(value="N/D")
        self.logged_user = tk.StringVar(value="N/D")
        self.num_processes = tk.StringVar(value="N/D")
        self.num_open_ports = tk.StringVar(value="N/D")
        self.load_avg = (0, 0, 0)  # Tuple per (1min, 5min, 15min)
        
        # Creazione della GUI
        self.create_widgets()
        self.update_dashboard()  # Aggiornamento iniziale
        # Pianifica aggiornamenti periodici
        self.after(UPDATE_INTERVAL_MS, self.update_dashboard)

    def create_widgets(self):
        # Header
        header = ttk.Label(self, text="System Audit Dashboard", font=("Helvetica", 24, "bold"), background="#343a40", foreground="white", anchor="center")
        header.pack(fill=tk.X)
        
        # Frame per i dati di sistema
        data_frame = ttk.Frame(self)
        data_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Informazioni sul sistema
        lbl_kernel = ttk.Label(data_frame, text="Kernel Version:")
        lbl_kernel.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.val_kernel = ttk.Label(data_frame, textvariable=self.kernel_version)
        self.val_kernel.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        lbl_os = ttk.Label(data_frame, text="OS:")
        lbl_os.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.val_os = ttk.Label(data_frame, textvariable=self.os_info)
        self.val_os.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        lbl_user = ttk.Label(data_frame, text="Logged-in User:")
        lbl_user.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.val_user = ttk.Label(data_frame, textvariable=self.logged_user)
        self.val_user.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        lbl_processi = ttk.Label(data_frame, text="Number of Processes:")
        lbl_processi.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.val_processi = ttk.Label(data_frame, textvariable=self.num_processes)
        self.val_processi.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        lbl_ports = ttk.Label(data_frame, text="Open Ports:")
        lbl_ports.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.val_ports = ttk.Label(data_frame, textvariable=self.num_open_ports)
        self.val_ports.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        lbl_load = ttk.Label(data_frame, text="Load Average (1m/5m/15m):")
        lbl_load.grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.val_load = ttk.Label(data_frame, text="N/D")
        self.val_load.grid(row=2, column=3, sticky="w", padx=5, pady=5)
        
        # Pulsante di aggiornamento manuale
        btn_refresh = ttk.Button(self, text="Aggiorna Dati", command=self.update_dashboard)
        btn_refresh.pack(pady=5)
        
        # Frame per il grafico
        graph_frame = ttk.LabelFrame(self, text="Load Average Graph")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Creazione della figura Matplotlib
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Load Average")
        self.ax.set_ylim(0, 5)  # Valore massimo arbitrario; si può adattare
        self.ax.set_xticks([0, 1, 2])
        self.ax.set_xticklabels(["1 min", "5 min", "15 min"])
        self.bars = self.ax.bar([0, 1, 2], [0, 0, 0], color="skyblue")
        
        # Incorpora la figura in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Area per i log/testo di output
        self.text_output = ScrolledText(self, wrap=tk.WORD, height=8)
        self.text_output.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.text_output.insert(tk.END, "Sistema monitorato: aggiornamento in corso...\n")
        
    def update_dashboard(self):
        """Aggiorna le informazioni di sistema e il grafico."""
        try:
            # Kernel version
            kernel = subprocess.check_output("uname -r", shell=True, universal_newlines=True).strip()
            self.kernel_version.set(kernel)
            logger.debug(f"Kernel: {kernel}")
        except Exception as e:
            self.kernel_version.set("Errore")
            logger.error(f"Errore nel recupero del kernel: {e}")
        
        try:
            # OS info
            os_info = platform.platform()
            self.os_info.set(os_info)
            logger.debug(f"OS: {os_info}")
        except Exception as e:
            self.os_info.set("Errore")
            logger.error(f"Errore nel recupero dell'OS: {e}")

        try:
            # Logged-in user
            user = getpass.getuser()
            self.logged_user.set(user)
            logger.debug(f"User: {user}")
        except Exception as e:
            self.logged_user.set("Errore")
            logger.error(f"Errore nel recupero dell'utente: {e}")

        try:
            # Numero di processi
            ps_output = subprocess.check_output("ps aux", shell=True, universal_newlines=True)
            n_processes = len(ps_output.splitlines()) - 1  # sottrai l'intestazione
            self.num_processes.set(n_processes)
            logger.debug(f"Number of processes: {n_processes}")
        except Exception as e:
            self.num_processes.set("Errore")
            logger.error(f"Errore nel recupero dei processi: {e}")

        try:
            # Numero di porte aperte: prova netstat, se non funziona usa ss
            try:
                ports_output = subprocess.check_output("netstat -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            except Exception:
                ports_output = subprocess.check_output("ss -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            # Conta le linee che sembrano contenere porte; togli l'intestazione
            port_lines = ports_output.splitlines()[2:]
            n_ports = len(port_lines)
            self.num_open_ports.set(n_ports)
            logger.debug(f"Open ports: {n_ports}")
        except Exception as e:
            self.num_open_ports.set("Errore")
            logger.error(f"Errore nel recupero delle porte aperte: {e}")
        
        try:
            # Load Average
            load1, load5, load15 = os.getloadavg()
            load_text = f"{load1:.2f} / {load5:.2f} / {load15:.2f}"
            self.val_load.config(text=load_text)
            self.load_avg = (load1, load5, load15)
            logger.debug(f"Load average: {self.load_avg}")
        except Exception as e:
            self.val_load.config(text="Errore")
            logger.error(f"Errore nel recupero del load average: {e}")
        
        self.update_graph()
        self.text_output.insert(tk.END, f"Dashboard aggiornata alle {time.strftime('%H:%M:%S')}.\n")
        self.after(UPDATE_INTERVAL_MS, self.update_dashboard)  # Ripianifica l'aggiornamento

    def update_graph(self):
        """Aggiorna il grafico a barre con i dati del load average."""
        try:
            # Aggiorna le barre con i valori attuali del load average
            values = list(self.load_avg)
            for bar, val in zip(self.bars, values):
                bar.set_height(val)
            # Aggiorna il limite superiore dell'asse y se necessario
            max_val = max(values) if values else 5
            self.ax.set_ylim(0, max(max_val * 1.2, 5))
            self.canvas.draw()
            logger.debug("Grafico aggiornato.")
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento del grafico: {e}")

if __name__ == "__main__":
    app = SystemAuditDashboard()
    app.mainloop()
