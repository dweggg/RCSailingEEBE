#!/usr/bin/env python3
"""
e-Tech Sailing Telemetry GUI
===========================

Main application entry point for the telemetry visualization system.
"""

import sys
import time
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui

# Import from the refactored telemetry_gui package
from telemetry_gui.utils.config import CONFIG
from telemetry_gui.data.signals import SignalDefinitions, SignalsList
from telemetry_gui.data.data_manager import DataManager
from telemetry_gui.communication.comm_manager import CommunicationManager, SerialProtocol
from telemetry_gui.ui.focus_manager import FocusManager
from telemetry_gui.ui.logger_widget import CSVLoggerWidget, TerminalLogWidget
from telemetry_gui.ui.plot_widget import DynamicPlot
from telemetry_gui.ui.tiling_area import TilingArea
from telemetry_gui.ui.menu_system import setup_menu_system


class TelemetryApplication:
    """Main application class for the telemetry GUI."""
    
    def __init__(self):
        """Initialize the application and its components."""
        # Create the application instance
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setApplicationName("e-Tech Sailing Telemetry Logger")
        
        # Initialize core subsystems
        self.signal_definitions = SignalDefinitions(CONFIG['database_file'])
        self.data_manager = DataManager(max_points=CONFIG['max_points'])
        self.data_manager.initialize_signals(self.signal_definitions.get_all_keys())
        
        # Initialize communication
        self.comm_manager = CommunicationManager(
            protocol=SerialProtocol(baud_rate=CONFIG['baud_rate'])
        )
        
        # Register data callback
        self.comm_manager.register_data_callback(self._on_data_received)
        
        # Flag to freeze/unfreeze plot updates
        self.freeze_plots = False
        
        # Setup UI
        self._setup_ui()
        
        # Setup timer for periodic updates
        self._setup_timers()
        
    def _setup_ui(self):
        """Setup the application's user interface."""
        # Main window setup
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setWindowTitle("e-Tech Sailing Telemetry Logger")
        self.main_window.resize(1400, 800)
        
        # Create central widget and layout
        self.central_widget = QtWidgets.QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        central_layout = QtWidgets.QHBoxLayout(self.central_widget)
        
        # --- Left Column: Variables List, Logger and Terminal ---
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        # Create widgets for the left panel
        self.terminal_log = TerminalLogWidget()
        
        signals_group = QtWidgets.QGroupBox("Signals")
        signals_layout = QtWidgets.QVBoxLayout(signals_group)
        self.signals_list = SignalsList(self.signal_definitions)
        signals_layout.addWidget(self.signals_list)
        
        self.csv_logger = CSVLoggerWidget(self.data_manager)
        
        # Add widgets to the left panel with proportional sizes
        left_layout.addWidget(self.terminal_log, 1)  # Smaller
        left_layout.addWidget(signals_group, 2)      # Larger
        left_layout.addWidget(self.csv_logger, 1)    # Smaller
        
        # --- Right Column: Plot Area (Tiling Area) ---
        self.tiling_area = TilingArea()
        # Provide data and communication managers to tiling area for plot creation
        self.tiling_area.data_manager = self.data_manager
        self.tiling_area.comm_manager = self.comm_manager
        
        # --- Create Horizontal Splitter ---
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        central_layout.addWidget(self.main_splitter)
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(self.tiling_area)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        
        # Setup menu system
        self.menu_system = setup_menu_system(self.main_window, self.tiling_area)
        
        # Connect menu actions that should interact with the application
        self._connect_menu_actions()
        
        # Setup status indicators
        self._setup_indicators()
        
        # Connect signals
        self._connect_signals()
        
        # Initial plots
        self.tiling_area.add_initial_row()
        
        # Redirect stdout/stderr to our terminal_log widget
        sys.stdout = self.terminal_log
        sys.stderr = self.terminal_log
        
        # Print startup message
        print(f"e-Tech Sailing Telemetry Logger started")
        
    def _connect_menu_actions(self):
        """Connect menu actions that should interact with the main application."""
        # Find the "Clear All Data" action and connect it to our handler
        for action in self.main_window.findChildren(QtGui.QAction):
            if action.text() == "Clear &All Data":
                action.triggered.connect(self._clear_all_data)
                
    def _setup_indicators(self):
        """Setup status indicators in the menu bar."""
        # Freeze indicator (shows pause status)
        self.freeze_indicator = QtWidgets.QLabel()
        self.freeze_indicator.setFixedSize(20, 20)
        self.freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")
        self.freeze_indicator.setToolTip("Plot Updates Status: Running")
        
        # Connection indicator (button to toggle connection)
        self.connection_indicator = QtWidgets.QPushButton("")
        self.connection_indicator.setFixedSize(20, 20)
        self.connection_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
        self.connection_indicator.setFlat(True)
        self.connection_indicator.setToolTip("Serial Connection: Disconnected")
        
        # Status text
        self.status_label = QtWidgets.QLabel("Ready")
        
        # Container for indicators with some margins
        corner_container = QtWidgets.QWidget()
        corner_layout = QtWidgets.QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(5, 0, 5, 0)
        corner_layout.setSpacing(10)
        corner_layout.addWidget(self.status_label)
        corner_layout.addWidget(self.freeze_indicator)
        corner_layout.addWidget(self.connection_indicator)
        
        # Add to menu bar
        self.main_window.menuBar().setCornerWidget(corner_container, QtCore.Qt.Corner.TopRightCorner)
        
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Connection indicator click
        self.connection_indicator.clicked.connect(self._toggle_connection)
        
        # Signal list double-click
        self.signals_list.itemDoubleClicked.connect(self._add_variable_to_selected)
        
        # Override key press event for spacebar to freeze/unfreeze
        self.original_keyPressEvent = self.main_window.keyPressEvent
        self.main_window.keyPressEvent = self._custom_keyPressEvent
        
    def _setup_timers(self):
        """Setup timers for periodic updates."""
        # Main timer for status updates
        self.main_timer = QtCore.QTimer()
        self.main_timer.timeout.connect(self._update)
        self.main_timer.start(CONFIG['update_interval_ms'])
        
        # Plot timer for visualization updates
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self._update_plots)
        self.plot_timer.start(CONFIG['plot_update_interval_ms'])
        
    def _on_data_received(self, key, value, timestamp):
        """
        Handle received data from the communication manager.
        
        Args:
            key: Signal key
            value: Signal value
            timestamp: Receive timestamp
        """
        # Add to the data store
        self.data_manager.add_data_point(key, value)
        
    def _update(self):
        """Periodic update for logging and indicators."""
        # Log data point if logging is active
        self.data_manager.log_data_point()
        
        # Update indicators
        self._update_indicators()
        
    def _update_plots(self):
        """Update the plot displays."""
        if not self.freeze_plots:
            for plot in self.tiling_area.plots.keys():
                plot.update_plot()
                
    def _update_indicators(self):
        """Update status indicators."""
        # Connection status
        if not self.comm_manager.is_connected():
            self.connection_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
            self.connection_indicator.setToolTip("Serial Connection: Disconnected")
        elif time.time() - self.comm_manager.last_ok_time > 1.0:
            self.connection_indicator.setStyleSheet("background-color: orange; border-radius: 10px;")
            self.connection_indicator.setToolTip("Serial Connection: No heartbeat")
        else:
            self.connection_indicator.setStyleSheet("background-color: green; border-radius: 10px;")
            self.connection_indicator.setToolTip("Serial Connection: Connected")
        
        # Freeze status
        if self.freeze_plots:
            self.freeze_indicator.setStyleSheet("background-color: blue; border-radius: 10px;")
            self.freeze_indicator.setToolTip("Plot Updates: Paused (Press Space to resume)")
        else:
            self.freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")
            self.freeze_indicator.setToolTip("Plot Updates: Running (Press Space to pause)")
            
    def _toggle_connection(self):
        """Toggle the communication connection state."""
        is_connected = self.comm_manager.toggle_connection()
        self.status_label.setText("Connected" if is_connected else "Disconnected")
        
    def _add_variable_to_selected(self, item):
        """
        Add or remove a variable to the currently selected widget.
        
        Args:
            item: List item containing the signal information
        """
        signal = item.data(QtCore.Qt.ItemDataRole.UserRole)
        active_widget = FocusManager.get_active()
        
        if active_widget is None:
            self.status_label.setText("Select a plot or logger first")
            return
            
        if isinstance(active_widget, CSVLoggerWidget):
            active_widget.toggle_signal(signal)
            self.status_label.setText(f"Toggled {signal} in Logger")
        elif isinstance(active_widget, DynamicPlot):
            if signal not in active_widget.signal_keys_assigned:
                active_widget.add_signal(signal)
                self.status_label.setText(f"Added {signal} to plot")
            else:
                active_widget.remove_signal(signal)
                self.status_label.setText(f"Removed {signal} from plot")
        else:
            self.status_label.setText("Cannot add signals to this widget")
                
    def _custom_keyPressEvent(self, event):
        """
        Handle custom key press events.
        
        Args:
            event: Key press event
        """
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.freeze_plots = not self.freeze_plots
            self.status_label.setText("Plot updates paused" if self.freeze_plots else "Plot updates resumed")
        else:
            self.original_keyPressEvent(event)
            
    def _clear_all_data(self):
        """Clear all data from the application."""
        reply = QtWidgets.QMessageBox.question(
            self.main_window, "Clear All Data",
            "Are you sure you want to clear all data?",
            QtWidgets.QMessageBox.StandardButton.Yes | 
            QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.data_manager.clear_data()
            self.status_label.setText("All data cleared")
            
    def run(self):
        """Run the application."""
        # Show the main window
        self.main_window.show()
        
        # Exit when app execution ends
        return self.app.exec()
        

# Entry point
if __name__ == "__main__":
    app = TelemetryApplication()
    sys.exit(app.run())
