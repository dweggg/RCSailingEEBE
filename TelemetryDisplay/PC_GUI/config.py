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
MAX_POINTS = 2000             # Maximum data points to store per channel
MODEL_PATH = 'boat_model.STL'
