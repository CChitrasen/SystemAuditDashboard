#!/usr/bin/env python3
"""
System Audit Dashboard - (Italiano)
-----------------------------------------------------
Una dashboard centralizzata per il monitoraggio dei sistemi Linux che fornisce una panoramica in tempo reale delle informazioni chiave:
  - Versione del kernel
  - Dettagli del sistema operativo
  - Utente loggato
  - Numero di processi attivi
  - Numero di porte aperte
  - Load average (1 min, 5 min, 15 min)
  - Memoria disponibile (in MB)
  - Utilizzo del disco (percentuale su /)

La dashboard include:
  - Un grafico a barre (utilizzando Matplotlib) per visualizzare il load average.
  - Un intervallo di aggiornamento configurabile in secondi.
  - Raccolta dati eseguita in un thread separato per mantenere la GUI reattiva.
  - Aggiornamenti periodici tramite Tkinter e registrazione di tutti gli eventi nel log ("sys_audit_dashboard.log").

Autore: Bocaletto Luca
Licenza: GPL
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

# Importa Matplotlib per il grafico
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    messagebox.showerror("Errore", "Matplotlib non è installato. Installalo tramite pip e riprova.")
    exit(1)

# Configurazione del logging
logging.basicConfig(
    filename="sys_audit_dashboard.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("System Audit Dashboard avviato.")

# Directory da escludere durante la scansione
EXCLUDE_DIRS = ["/proc", "/sys", "/dev"]

class SystemAuditDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Audit Dashboard")
        self.geometry("1000x750")
        self.configure(bg="white")
        # Variabili Tkinter per le informazioni di sistema
        self.kernel_var = tk.StringVar(value="N/D")
        self.os_var = tk.StringVar(value="N/D")
        self.user_var = tk.StringVar(value="N/D")
        self.processes_var = tk.StringVar(value="N/D")
        self.ports_var = tk.StringVar(value="N/D")
        self.load_var = tk.StringVar(value="N/D")
        self.memory_var = tk.StringVar(value="N/D")
        self.disk_var = tk.StringVar(value="N/D")
        # Intervallo di aggiornamento in secondi (configurabile dall'utente)
        self.interval_sec = tk.IntVar(value=60)
        self.interval_ms = self.interval_sec.get() * 1000
        
        # Valori del load average (tuple: (1m, 5m, 15m))
        self.load_values = (0, 0, 0)
        
        self.create_widgets()
        # Avvia l'aggiornamento della dashboard
        self.update_dashboard()

    def create_widgets(self):
        # Header
        header = ttk.Label(self, text="System Audit Dashboard", font=("Helvetica", 24, "bold"),
                           background="#343a40", foreground="white", anchor="center")
        header.pack(fill=tk.X)
        
        # Frame per la configurazione dell'intervallo di aggiornamento
        frame_config = ttk.Frame(self)
        frame_config.pack(fill=tk.X, padx=10, pady=5)
        lbl_interval = ttk.Label(frame_config, text="Intervallo di aggiornamento (sec):")
        lbl_interval.pack(side=tk.LEFT, padx=5)
        self.entry_interval = ttk.Entry(frame_config, textvariable=self.interval_sec, width=5)
        self.entry_interval.pack(side=tk.LEFT, padx=5)
        btn_set_interval = ttk.Button(frame_config, text="Imposta", command=self.set_interval)
        btn_set_interval.pack(side=tk.LEFT, padx=5)
        
        # Frame per le informazioni di sistema
        frame_info = ttk.Frame(self)
        frame_info.pack(padx=10, pady=5, fill=tk.X)
        
        # Colonna 1: Kernel, OS e Utente
        lbl_kernel = ttk.Label(frame_info, text="Versione del Kernel:")
        lbl_kernel.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.val_kernel = ttk.Label(frame_info, textvariable=self.kernel_var)
        self.val_kernel.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        lbl_os = ttk.Label(frame_info, text="Sistema Operativo:")
        lbl_os.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.val_os = ttk.Label(frame_info, textvariable=self.os_var)
        self.val_os.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        lbl_user = ttk.Label(frame_info, text="Utente Loggato:")
        lbl_user.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.val_user = ttk.Label(frame_info, textvariable=self.user_var)
        self.val_user.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Colonna 2: Processi, Porte e Load Average
        lbl_processes = ttk.Label(frame_info, text="Numero di Processi:")
        lbl_processes.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.val_processes = ttk.Label(frame_info, textvariable=self.processes_var)
        self.val_processes.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        lbl_ports = ttk.Label(frame_info, text="Porte Aperte:")
        lbl_ports.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.val_ports = ttk.Label(frame_info, textvariable=self.ports_var)
        self.val_ports.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        lbl_load = ttk.Label(frame_info, text="Load Average (1m/5m/15m):")
        lbl_load.grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.val_load = ttk.Label(frame_info, textvariable=self.load_var)
        self.val_load.grid(row=2, column=3, sticky="w", padx=5, pady=5)
        
        # Colonna 3: Memoria disponibile e Utilizzo del disco
        lbl_memory = ttk.Label(frame_info, text="Memoria Disponibile:")
        lbl_memory.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.val_memory = ttk.Label(frame_info, textvariable=self.memory_var)
        self.val_memory.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        lbl_disk = ttk.Label(frame_info, text="Utilizzo Disco (/):")
        lbl_disk.grid(row=3, column=2, sticky="w", padx=5, pady=5)
        self.val_disk = ttk.Label(frame_info, textvariable=self.disk_var)
        self.val_disk.grid(row=3, column=3, sticky="w", padx=5, pady=5)
        
        # Pulsante di aggiornamento manuale
        btn_refresh = ttk.Button(self, text="Aggiornamento Manuale", command=self.update_dashboard)
        btn_refresh.pack(pady=5)
        
        # Frame per il grafico del Load Average
        frame_graph = ttk.LabelFrame(self, text="Grafico Load Average")
        frame_graph.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Load Average")
        self.ax.set_ylim(0, 5)
        self.ax.set_xticks([0, 1, 2])
        self.ax.set_xticklabels(["1 min", "5 min", "15 min"])
        self.bars = self.ax.bar([0, 1, 2], [0, 0, 0], color="skyblue")
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame_graph)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Area di output per log/informazioni
        self.text_output = ScrolledText(self, wrap=tk.WORD, height=8)
        self.text_output.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.text_output.insert(tk.END, "Inizializzazione della dashboard in corso...\n")
    
    def set_interval(self):
        """
        Aggiorna l'intervallo di aggiornamento in base al valore inserito.
        """
        try:
            sec = int(self.entry_interval.get())
            self.interval_sec.set(sec)
            self.interval_ms = sec * 1000
            self.text_output.insert(tk.END, f"Intervallo aggiornato a {sec} secondi.\n")
        except Exception as e:
            messagebox.showerror("Errore", "Inserisci un valore numerico valido per l'intervallo.")

    def thread_update(self):
        """
        Funzione eseguita in un thread separato per raccogliere le informazioni di sistema.
        """
        data = {}
        try:
            data["kernel"] = subprocess.check_output("uname -r", shell=True, universal_newlines=True).strip()
        except Exception as e:
            data["kernel"] = "Errore"
            logger.error(f"Errore nel recupero del kernel: {e}")
        try:
            data["os"] = platform.platform()
        except Exception as e:
            data["os"] = "Errore"
            logger.error(f"Errore nel recupero dell'OS: {e}")
        try:
            data["user"] = getpass.getuser()
        except Exception as e:
            data["user"] = "Errore"
            logger.error(f"Errore nel recupero dell'utente: {e}")
        try:
            ps_output = subprocess.check_output("ps aux", shell=True, universal_newlines=True)
            data["processes"] = len(ps_output.splitlines()) - 1
        except Exception as e:
            data["processes"] = "Errore"
            logger.error(f"Errore nel recupero dei processi: {e}")
        try:
            try:
                ports_output = subprocess.check_output("netstat -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            except Exception:
                ports_output = subprocess.check_output("ss -tulpn 2>/dev/null", shell=True, universal_newlines=True)
            port_lines = ports_output.splitlines()[2:]
            data["ports"] = len(port_lines)
        except Exception as e:
            data["ports"] = "Errore"
            logger.error(f"Errore nel recupero delle porte aperte: {e}")
        try:
            data["load"] = os.getloadavg()
        except Exception as e:
            data["load"] = (0, 0, 0)
            logger.error(f"Errore nel recupero del load average: {e}")
        try:
            free_output = subprocess.check_output("free -m", shell=True, universal_newlines=True)
            for line in free_output.splitlines():
                if line.startswith("Mem:"):
                    parts = line.split()
                    data["memory"] = parts[6] + " MB"
                    break
        except Exception as e:
            data["memory"] = "Errore"
            logger.error(f"Errore nel recupero della memoria: {e}")
        try:
            df_output = subprocess.check_output("df -h /", shell=True, universal_newlines=True)
            lines = df_output.splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                data["disk"] = parts[4]
            else:
                data["disk"] = "N/D"
        except Exception as e:
            data["disk"] = "Errore"
            logger.error(f"Errore nel recupero dell'utilizzo del disco: {e}")
        return data

    def update_gui(self, data):
        """
        Aggiorna le variabili Tkinter e il grafico con i dati raccolti.
        """
        self.kernel_var.set(data.get("kernel", "N/D"))
        self.os_var.set(data.get("os", "N/D"))
        self.user_var.set(data.get("user", "N/D"))
        self.processes_var.set(data.get("processes", "N/D"))
        self.ports_var.set(data.get("ports", "N/D"))
        load = data.get("load", (0, 0, 0))
        self.load_values = load
        self.load_var.set(f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}")
        self.memory_var.set(data.get("memory", "N/D"))
        self.disk_var.set(data.get("disk", "N/D"))
        self.update_graph()
        now = time.strftime("%H:%M:%S")
        self.text_output.insert(tk.END, f"Dashboard aggiornata alle {now}.\n")
        self.lbl_status.config(text="Dashboard aggiornata.")

    def thread_update_wrapper(self):
        """
        Funzione wrapper eseguita in un thread per aggiornare la GUI in modo thread-safe.
        """
        data = self.thread_update()
        self.after(0, lambda: self.update_gui(data))
    
    def update_dashboard(self):
        """
        Avvia un thread per aggiornare la dashboard e pianifica il prossimo aggiornamento in base all'intervallo impostato.
        """
        threading.Thread(target=self.thread_update_wrapper, daemon=True).start()
        self.after(self.interval_ms, self.update_dashboard)
    
    def update_graph(self):
        """
        Aggiorna il grafico a barre con i valori attuali del load average.
        """
        try:
            values = list(self.load_values)
            for bar, val in zip(self.bars, values):
                bar.set_height(val)
            max_val = max(values) if values else 5
            self.ax.set_ylim(0, max(max_val * 1.2, 5))
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento del grafico: {e}")

if __name__ == "__main__":
    app = SystemAuditDashboard()
    app.mainloop()
