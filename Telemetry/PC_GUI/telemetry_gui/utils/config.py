"""
Configuration Module
===================

This module manages application configuration parameters like baud rate, 
update intervals, and cross-platform settings.
"""

import os
import sys
import json
from pathlib import Path

# --- Cross-Platform Configuration ---
def configure_platform_settings():
    """Configure platform-specific settings."""
    if sys.platform.startswith('linux'):
        if "WAYLAND_DISPLAY" in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"

# Call this function when the module is imported
configure_platform_settings()

# --- Default File Paths ---
ROOT_DIR = Path(__file__).parent.parent.parent
RESOURCES_DIR = ROOT_DIR
DATABASE_FILE = ROOT_DIR / 'database.json'
DEFAULT_LAYOUT_FILE = ROOT_DIR / 'default_layout.json'

# --- Communication Settings ---
BAUD_RATE = 115200

# --- UI & Performance Settings ---
UPDATE_INTERVAL_MS = 5       # Main update interval in milliseconds
PLOT_UPDATE_INTERVAL_MS = 30 # Plot update interval
MAX_POINTS = 5000            # Maximum data points to store per channel

# --- Function to load configuration from a file ---
def load_config(config_file=None):
    """
    Load configuration from a JSON file if it exists, otherwise use defaults.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        dict: Dictionary with configuration parameters
    """
    config = {
        'baud_rate': BAUD_RATE,
        'update_interval_ms': UPDATE_INTERVAL_MS,
        'plot_update_interval_ms': PLOT_UPDATE_INTERVAL_MS,
        'max_points': MAX_POINTS,
        'database_file': str(DATABASE_FILE),
        'default_layout_file': str(DEFAULT_LAYOUT_FILE)
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {e}")
    
    return config

# Default configuration
CONFIG = load_config()