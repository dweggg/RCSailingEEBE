"""
Data Manager Module
==================

This module handles data storage, management, and logging for telemetry signals.
"""

import time
import csv
from typing import Dict, List, Tuple, Optional
from PyQt6 import QtWidgets

class DataManager:
    """
    Manages telemetry data storage and logging operations.
    """
    
    def __init__(self, max_points: int = 5000):
        """
        Initialize the DataManager.
        
        Args:
            max_points: Maximum number of data points to store per signal
        """
        self.max_points = max_points
        self.data_history: Dict[str, List[Tuple[float, float]]] = {}
        self.start_time = time.time()
        
        # CSV logging state
        self.logging_active = False
        self.logging_start_time = None
        self.logging_vars: List[str] = []
        self.csv_file = None
        self.csv_writer = None
    
    def initialize_signals(self, signal_keys: Dict[str, Dict]):
        """
        Initialize data storage for the provided signal keys.
        
        Args:
            signal_keys: Dictionary of signal keys
        """
        self.data_history = {key: [] for key in signal_keys}
    
    def add_data_point(self, signal: str, value: float) -> None:
        """
        Add a data point for a signal with the current timestamp.
        
        Args:
            signal: Signal identifier
            value: Value to record
        """
        if signal not in self.data_history:
            self.data_history[signal] = []
        
        timestamp = time.time() - self.start_time
        self.data_history[signal].append((value, timestamp))
        
        # Trim data if exceeding max points
        if len(self.data_history[signal]) > self.max_points:
            self.data_history[signal] = self.data_history[signal][-self.max_points:]
    
    def get_signal_data(self, signal: str) -> List[Tuple[float, float]]:
        """
        Get all data points for a specific signal.
        
        Args:
            signal: Signal identifier
            
        Returns:
            List of (value, timestamp) tuples
        """
        return self.data_history.get(signal, [])
    
    def get_latest_value(self, signal: str) -> Optional[float]:
        """
        Get the latest value for a specific signal.
        
        Args:
            signal: Signal identifier
            
        Returns:
            The latest value or None if no data
        """
        data = self.data_history.get(signal, [])
        if data:
            return data[-1][0]
        return None
    
    def clear_data(self) -> None:
        """Clear all stored data."""
        for key in self.data_history:
            self.data_history[key] = []
    
    def current_time(self) -> float:
        """
        Get the elapsed time since the DataManager was initialized.
        
        Returns:
            Time in seconds since start of data collection.
        """
        return time.time() - self.start_time

    def start_logging(self, signals: List[str]) -> bool:
        """
        Start CSV logging for the specified signals.
        
        Args:
            signals: List of signal identifiers to log
            
        Returns:
            True if successfully started, False otherwise
        """
        if self.logging_active:
            return False
        
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save CSV Log", "", "CSV Files (*.csv)"
        )
        if not fname:
            return False
            
        try:
            self.csv_file = open(fname, 'w', newline='')
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Could not open file:\n{e}")
            return False
            
        self.csv_writer = csv.writer(self.csv_file)
        self.logging_vars = signals
        
        # Write header with time and the selected signal keys
        header = ["t"] + self.logging_vars
        self.csv_writer.writerow(header)
        self.csv_file.flush()
        
        self.logging_start_time = time.time()
        self.logging_active = True
        return True
    
    def stop_logging(self) -> None:
        """Stop CSV logging if active."""
        if not self.logging_active:
            return
            
        self.logging_active = False
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
    
    def log_data_point(self) -> None:
        """Log current data values if logging is active."""
        if not self.logging_active or not self.csv_writer:
            return
            
        t_ms = time.time() - self.logging_start_time
        row = [t_ms]
        
        for signal in self.logging_vars:
            # Write the latest value for each signal (or an empty string if no data)
            value = self.get_latest_value(signal)
            row.append(value if value is not None else "")
            
        # Write the row to the CSV file
        self.csv_writer.writerow(row)
        self.csv_file.flush()
    
    def load_log_file(self) -> bool:
        """
        Load data from a CSV log file.
        
        Returns:
            True if successfully loaded, False otherwise
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open CSV Log", "", "CSV Files (*.csv)"
        )
        if not fname:
            return False
            
        # Clear existing data
        self.clear_data()
        
        try:
            with open(fname, 'r') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return False
                    
                signals = header[1:]
                for signal in signals:
                    self.data_history[signal] = []
                    
                for row in reader:
                    t_val = float(row[0]) if row[0] else 0
                    for i, signal in enumerate(signals, start=1):
                        if i < len(row) and row[i]:
                            try:
                                val = float(row[i])
                                self.data_history[signal].append((val, t_val))
                            except ValueError:
                                pass  # Skip non-numeric values
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Error loading log file:\n{e}")
            return False