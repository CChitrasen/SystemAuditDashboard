# SystemAuditDashboard
#### Author: Bocaletto Luca

SystemAuditDashboard is a centralized Linux system monitoring dashboard implemented in Python using Tkinter. It provides a real-time overview of key system information including:

- **Kernel Version**  
- **Operating System Details**  
- **Logged-in User**  
- **Number of Active Processes**  
- **Number of Open Ports**  
- **Load Average (1 min, 5 min, 15 min)**  
- **Available Memory (in MB)**  
- **Disk Usage (percentage on the root partition)**  

Additionally, the dashboard features an interactive bar chart (via Matplotlib) to visualize the load average, and it supports a configurable update interval. Data collection is executed in a separate thread to ensure that the GUI remains responsive during periodic updates.

## Features

- **Threaded Data Collection:**  
  System information is gathered in a separate thread, ensuring a responsive and non-blocking GUI.

- **Configurable Update Interval:**  
  The update interval (in seconds) can be set by the user via the dashboard interface.

- **Real-Time Monitoring:**  
  The dashboard provides live system metrics, including load average, which are dynamically displayed within the GUI.

- **Interactive Graph:**  
  A Matplotlib bar chart visualizes the load average values for 1 min, 5 min, and 15 min, updating automatically with each refresh.

- **Comprehensive Logging:**  
  All operations and potential errors are logged to `sys_audit_dashboard.log` for troubleshooting and auditing.

## Requirements

- **Python 3.x**
- **Linux System (Designed for Linux)**
- Standard libraries and the following Python packages:
  - **Tkinter** (usually included with Python on Linux)
  - **Matplotlib**

To install Matplotlib (if not already installed), run:

```bash
pip install matplotlib
```

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/bocaletto-luca/SystemAuditDashboard.git
   cd SystemAuditDashboard
   ```

2. **Configure (Optional):**  
   You may change the default update interval by entering a new value (in seconds) in the dashboard interface.

## Usage

There are two versions available:
- **main_eng.py** – The English version.
- **main_ita.py** – The Italian version.

To run the English version, execute:

```bash
python3 main_eng.py
```

*Note:* It is recommended to run this tool with appropriate privileges (e.g., as root) to ensure complete access to all system information.

## How It Works

SystemAuditDashboard gathers various system metrics by executing common Linux commands and Python system calls. It then updates the GUI with the following information:
- The kernel version is obtained via `uname -r`.
- OS details are provided by Python’s platform module.
- The logged-in user is retrieved using `getpass.getuser()`.
- Active processes are counted using `ps aux`.
- Open ports are determined using `netstat` or `ss`.
- Load averages are acquired with `os.getloadavg()`.
- Available memory is extracted from the output of `free -m`.
- Disk usage is determined via `df -h /`.

The dashboard periodically refreshes using Tkinter’s `after()` method and displays updated values along with an interactive load average graph.

## Contributing

Contributions are welcome! If you find a bug, have an improvement suggestion, or want to add new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the GNU General Public License (GPL). See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, issues, or further collaboration, please open an issue in the [GitHub Issues](https://github.com/bocaletto-luca/SystemAuditDashboard/issues) section or contact me.

---

Happy Monitoring and Secure Coding!

---
