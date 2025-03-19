from config import SENSOR_KEYS

# --- Data Storage ---
data_history = {key: [] for key in SENSOR_KEYS}

# --- Global variables for CSV Logging ---
logging_active = False
logging_start_time = None
logging_vars = []  # List of sensor keys to log
csv_file = None
csv_writer = None
