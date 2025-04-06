#!/usr/bin/env python3
from config import BAUD_RATE, UPDATE_INTERVAL_MS, PLOT_UPDATE_INTERVAL_MS, MAX_POINTS

import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
import threading

from variables import SENSOR_KEYS
from data import data_history, start_time
from plot import DynamicPlot
from tiles import TilingArea
from logger import *
from focus import FocusManager
from menu import setup_menu_bar

# Import the new communication module
from comm import SerialComm, comm

# --- Global Logging Variables ---
logging_active = False
logging_start_time = None
logging_vars = []  # Captured sensor keys for logging when logging starts.
csv_file = None
csv_writer = None

# Global flag to freeze/unfreeze data updates.
freeze_plots = False

# --- Application Setup ---
app = QtWidgets.QApplication([])

# Main window setup
main_window = QtWidgets.QMainWindow()
main_window.setWindowTitle("e-Tech Sailing Telemetry Logger")
main_window.resize(1400, 800)

# Create the central widget and layout (we won't add the indicator here)
central_widget = QtWidgets.QWidget()
main_window.setCentralWidget(central_widget)
central_layout = QtWidgets.QHBoxLayout(central_widget)
central_widget.setLayout(central_layout)

# --- Left Column: Variables List and CSV Logger ---
left_widget = QtWidgets.QWidget()
left_layout = QtWidgets.QVBoxLayout(left_widget)
left_layout.setContentsMargins(5, 5, 5, 5)
left_layout.setSpacing(5)

variables_list = VariablesList()
left_layout.addWidget(variables_list)

csv_logger_widget = CSVLoggerWidget()
left_layout.addWidget(csv_logger_widget)

# --- Middle Column: Plot Area (Tiling Area) ---
tiling_area = TilingArea()

# --- Right Column: 3D Model View (Initially Hidden) ---


# --- Create Horizontal Splitter ---
main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
central_layout.addWidget(main_splitter)
main_splitter.addWidget(left_widget)
main_splitter.addWidget(tiling_area)
main_splitter.setStretchFactor(0, 1)
main_splitter.setStretchFactor(1, 3)
main_splitter.setStretchFactor(2, 1)


# --- Connect CSV Logger Button ---
csv_logger_widget.log_button.clicked.connect(lambda: toggle_logging(csv_logger_widget))

# --- Setup Menu Bar (called only once) ---
setup_menu_bar(main_window, tiling_area)

# --- Create Indicators in Menu Bar Corner ---
# Freeze indicator (shows pause status)
freeze_indicator = QtWidgets.QLabel()
freeze_indicator.setFixedSize(20, 20)  # enforce circular dimensions
freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")

# OK indicator (now a button to open the serial port selection popup)
ok_indicator = QtWidgets.QPushButton("")
ok_indicator.setFixedSize(20, 20)  # enforce circular dimensions
ok_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
ok_indicator.setFlat(True)

# Create the communication instance and wire up the connection button.
ok_indicator.clicked.connect(comm.change_connection)

# Container for both indicators with some margins.
corner_container = QtWidgets.QWidget()
corner_layout = QtWidgets.QHBoxLayout(corner_container)
corner_layout.setContentsMargins(5, 0, 5, 0)
corner_layout.setSpacing(10)
corner_layout.addWidget(freeze_indicator)
corner_layout.addWidget(ok_indicator)
main_window.menuBar().setCornerWidget(corner_container, QtCore.Qt.Corner.TopRightCorner)

def update():
    # Log data (every new data point has been appended by the serial thread).
    log_data(data_history)

    # Update indicators based on the communication connection and last OK time.
    if not comm.is_connected() or time.time() - comm.last_ok_time > 1:
        ok_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
    else:
        ok_indicator.setStyleSheet("background-color: green; border-radius: 10px;")

    if freeze_plots:
        freeze_indicator.setStyleSheet("background-color: blue; border-radius: 10px;")
    else:
        freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")

# --- Plot Update Function ---

def update_plots():
    if not freeze_plots:
        for plot in tiling_area.plots.keys():
            plot.update_plot(data_history)

# --- Timers ---

main_timer = QtCore.QTimer()
main_timer.timeout.connect(update)
main_timer.start(UPDATE_INTERVAL_MS)

plot_timer = QtCore.QTimer()
plot_timer.timeout.connect(update_plots)
plot_timer.start(PLOT_UPDATE_INTERVAL_MS)

def add_variable_to_selected(item):
    sensor = item.data(QtCore.Qt.ItemDataRole.UserRole)
    active_widget = FocusManager.get_active()
    if active_widget is None:
        return
    if isinstance(active_widget, CSVLoggerWidget):
        active_widget.toggle_sensor(sensor)
    else:
        if sensor not in active_widget.sensor_keys_assigned:
            active_widget.add_sensor(sensor)
        else:
            active_widget.remove_sensor(sensor)

variables_list.itemDoubleClicked.connect(add_variable_to_selected)

tiling_area.add_initial_row()

original_keyPressEvent = main_window.keyPressEvent
def custom_keyPressEvent(event):
    global freeze_plots
    if event.key() == QtCore.Qt.Key.Key_Space:
        freeze_plots = not freeze_plots
    else:
        original_keyPressEvent(event)
main_window.keyPressEvent = custom_keyPressEvent

# Start the communication reader thread
comm.start_reader()

main_window.show()
sys.exit(app.exec())
