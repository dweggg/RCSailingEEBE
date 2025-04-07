import json
from PyQt6 import QtWidgets, QtCore

DATABASE_FILE = 'database.json'

def load_signal_keys(database_file):
    """ Load signal keys from a JSON configuration file. """
    try:
        with open(database_file, 'r') as file:
            config = json.load(file)
            # Convert to a dictionary where key = signal key, and value = {dir, name}
            signal_dict = {
                signal["key"]: {"dir": signal["dir"], "name": signal["name"]}
                for signal in config.get("signal_keys", [])
            }
            return signal_dict
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        return {}

# Load signal keys as a dictionary
SIGNAL_KEYS = load_signal_keys(DATABASE_FILE)

class SignalsList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        # Populate the list with signal names
        for signal, info in SIGNAL_KEYS.items():
            item_text = f"{info['name']}"  # Show human-readable name + key
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, signal)  # Store signal key as metadata
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
            self.addItem(item)

def get_signal_direction(signal_key):
    """ Returns the direction (RX or TX) for the given signal key. """
    return SIGNAL_KEYS.get(signal_key, {}).get("dir", None)

def get_signal_name(signal_key):
    """ Returns the human-readable name for the given signal key. """
    return SIGNAL_KEYS.get(signal_key, {}).get("name", signal_key)  # Default to key if name is missing
