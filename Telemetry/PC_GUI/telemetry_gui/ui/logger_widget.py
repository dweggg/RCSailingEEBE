"""
Logger Widget Module
==================

Provides UI components for data logging and visualization.
"""

from PyQt6 import QtWidgets, QtCore
from typing import List, Callable, Optional

from telemetry_gui.ui.focus_manager import FocusManager
from telemetry_gui.data.data_manager import DataManager


class CSVLoggerWidget(QtWidgets.QGroupBox):
    """Widget for configuring and controlling CSV logging."""
    
    def __init__(self, data_manager: DataManager, title="CSV Logger", parent=None):
        """
        Initialize the CSV logger widget.
        
        Args:
            data_manager: Data manager instance to handle logging
            title: Widget title
            parent: Parent widget
        """
        super().__init__(title, parent)
        self.data_manager = data_manager
        self.selected = False  # Determines if this widget is "active"
        
        # Allow the widget to gain focus when clicked
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize the UI components."""
        # Vertical layout for the logger widget
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(10, 25, 10, 10)  # Margins: left, top, right, bottom
        
        # List widget to show selected signals
        self.signal_list_widget = QtWidgets.QListWidget()
        self.signal_list_widget.setMinimumHeight(100)  
        self.layout.addWidget(self.signal_list_widget)
        
        # Create horizontal layout for logging buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.log_button = QtWidgets.QPushButton("Start Logging")
        self.log_button.clicked.connect(self.toggle_logging)
        button_layout.addWidget(self.log_button)
        
        self.load_button = QtWidgets.QPushButton("Load Log")
        self.load_button.clicked.connect(self.load_log)
        button_layout.addWidget(self.load_button)
        
        self.layout.addLayout(button_layout)
        
        # Start with a gray border for the group box
        self.setStyleSheet("QGroupBox { border: 2px solid gray; }")
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events to set focus."""
        FocusManager.set_active(self)
        super().mousePressEvent(event)
    
    def add_signal(self, signal: str) -> None:
        """
        Add a signal to the logger list if not already present.
        
        Args:
            signal: Signal identifier to add
        """
        for index in range(self.signal_list_widget.count()):
            if self.signal_list_widget.item(index).text() == signal:
                return
        self.signal_list_widget.addItem(signal)
    
    def remove_signal(self, signal: str) -> None:
        """
        Remove a signal from the logger list.
        
        Args:
            signal: Signal identifier to remove
        """
        for index in range(self.signal_list_widget.count()):
            if self.signal_list_widget.item(index).text() == signal:
                self.signal_list_widget.takeItem(index)
                return
    
    def toggle_signal(self, signal: str) -> None:
        """
        Toggle a signal in the logger list (add if not present, remove if present).
        
        Args:
            signal: Signal identifier to toggle
        """
        found = False
        for index in range(self.signal_list_widget.count()):
            if self.signal_list_widget.item(index).text() == signal:
                found = True
                break
                
        if found:
            self.remove_signal(signal)
        else:
            self.add_signal(signal)
    
    def get_signals(self) -> List[str]:
        """
        Return a list of signal names currently selected for logging.
        
        Returns:
            List of selected signal identifiers
        """
        signals = []
        for index in range(self.signal_list_widget.count()):
            signals.append(self.signal_list_widget.item(index).text())
        return signals
    
    def toggle_logging(self) -> None:
        """Toggle CSV logging on/off."""
        if not self.data_manager.logging_active:
            # Get selected signals and start logging
            signals = self.get_signals()
            success = self.data_manager.start_logging(signals)
            
            if success:
                self.log_button.setText("Stop Logging")
                self.log_button.setStyleSheet("background-color: red; color: white;")
        else:
            # Stop logging
            self.data_manager.stop_logging()
            self.log_button.setText("Start Logging")
            self.log_button.setStyleSheet("")
    
    def load_log(self) -> None:
        """Load a CSV log file into the data manager."""
        success = self.data_manager.load_log_file()
        # The data manager handles showing dialog messages


class TerminalLogWidget(QtWidgets.QWidget):
    """Widget that displays log messages and can redirect stdout/stderr."""
    
    def __init__(self, parent=None):
        """
        Initialize the terminal log widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(1000)  # Limit scrollback to avoid memory issues
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_edit)
    
    def write(self, msg: str) -> None:
        """
        Append a message to the text edit (compatible with stdout/stderr).
        
        Args:
            msg: Message to display
        """
        self.text_edit.appendPlainText(msg.rstrip())
    
    def flush(self) -> None:
        """No-op flush method for stdout/stderr compatibility."""
        pass
    
    def clear(self) -> None:
        """Clear the log display."""
        self.text_edit.clear()