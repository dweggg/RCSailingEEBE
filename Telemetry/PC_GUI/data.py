from signals import SIGNAL_KEYS
import time

# --- Data Storage ---
data_history = {key: [] for key in SIGNAL_KEYS}
start_time = time.time()
 
# --- Global variables for CSV Logging ---
logging_active = False
logging_start_time = None
logging_vars = []  # List of signal keys to log
csv_file = None
csv_writer = None
