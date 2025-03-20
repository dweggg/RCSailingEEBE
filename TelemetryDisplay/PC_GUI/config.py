import os
import sys
import json

# --- Set Qt Platform Based on OS ---
if sys.platform.startswith('linux'):
    if "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland"
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

# --- Configuration ---
BAUD_RATE = 115200
UPDATE_INTERVAL_MS = 25      # Update interval in milliseconds
MAX_POINTS = 500             # Maximum data points to store per channel
MODEL_PATH = 'boat_model.stl'

# Load sensor keys from external JSON file
DATABASE_FILE = 'database.json'

def load_sensor_keys(database_file):
    """ Load sensor keys from a JSON configuration file. """
    try:
        with open(DATABASE_FILE, 'r') as file:
            config = json.load(file)
            return config.get("sensor_keys", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        return []

SENSOR_KEYS = load_sensor_keys(DATABASE_FILE)
