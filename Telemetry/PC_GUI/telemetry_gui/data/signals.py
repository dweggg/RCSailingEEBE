"""
Signals Module
=============

Manages signal definitions, metadata, and provides a list widget for signal selection.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6 import QtWidgets, QtCore

class SignalDefinitions:
    """Manages signal definitions and metadata."""
    
    def __init__(self, database_file: str):
        """
        Initialize signal definitions from a database file.
        
        Args:
            database_file: Path to the JSON database file with signal definitions
        """
        self.database_file = Path(database_file)
        self.signal_dict: Dict[str, Dict[str, str]] = {}
        self.load_signal_keys()
    
    def load_signal_keys(self) -> None:
        """Load signal keys from the JSON configuration file."""
        try:
            with open(self.database_file, 'r') as file:
                config = json.load(file)
                # Convert to a dictionary where key = signal key, and value = {dir, name}
                self.signal_dict = {
                    signal["key"]: {"dir": signal["dir"], "name": signal["name"]}
                    for signal in config.get("signal_keys", [])
                }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading signal database: {e}")
            self.signal_dict = {}
    
    def get_signal_direction(self, signal_key: str) -> Optional[str]:
        """
        Returns the direction (RX or TX) for the given signal key.
        
        Args:
            signal_key: The signal identifier
            
        Returns:
            Direction string or None if signal not found
        """
        return self.signal_dict.get(signal_key, {}).get("dir")
    
    def get_signal_name(self, signal_key: str) -> str:
        """
        Returns the human-readable name for the given signal key.
        
        Args:
            signal_key: The signal identifier
            
        Returns:
            Human-readable name or the key itself if not found
        """
        return self.signal_dict.get(signal_key, {}).get("name", signal_key)
    
    def get_all_keys(self) -> Dict[str, Dict[str, str]]:
        """
        Returns all signal keys and their metadata.
        
        Returns:
            Dictionary of signal keys and their metadata
        """
        return self.signal_dict


class SignalsList(QtWidgets.QListWidget):
    """Widget that displays a draggable list of available signals."""
    
    def __init__(self, signal_definitions: SignalDefinitions, parent=None):
        """
        Initialize the signals list widget.
        
        Args:
            signal_definitions: SignalDefinitions instance with signal metadata
            parent: Parent widget
        """
        super().__init__(parent)
        self.signal_definitions = signal_definitions
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.populate_list()
    
    def populate_list(self) -> None:
        """Populate the list with signal names from the definitions."""
        self.clear()
        for signal, info in self.signal_definitions.get_all_keys().items():
            item_text = f"{info['name']}"  # Show human-readable name
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, signal)  # Store signal key as metadata
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
            self.addItem(item)