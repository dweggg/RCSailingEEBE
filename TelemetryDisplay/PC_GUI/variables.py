import json
from PyQt6 import QtWidgets, QtCore

DATABASE_FILE = 'database.json'

def load_sensor_keys(database_file):
    """ Load sensor keys from a JSON configuration file. """
    try:
        with open(database_file, 'r') as file:
            config = json.load(file)
            # Convert to a dictionary where key = sensor key, and value = {dir, name}
            sensor_dict = {
                sensor["key"]: {"dir": sensor["dir"], "name": sensor["name"]}
                for sensor in config.get("sensor_keys", [])
            }
            return sensor_dict
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        return {}

# Load sensor keys as a dictionary
SENSOR_KEYS = load_sensor_keys(DATABASE_FILE)

class VariablesList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        # Populate the list with sensor names
        for sensor, info in SENSOR_KEYS.items():
            item_text = f"{info['name']}"  # Show human-readable name + key
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, sensor)  # Store sensor key as metadata
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
            self.addItem(item)

def get_sensor_direction(sensor_key):
    """ Returns the direction (RX or TX) for the given sensor key. """
    return SENSOR_KEYS.get(sensor_key, {}).get("dir", None)

def get_sensor_name(sensor_key):
    """ Returns the human-readable name for the given sensor key. """
    return SENSOR_KEYS.get(sensor_key, {}).get("name", sensor_key)  # Default to key if name is missing
