#!/usr/bin/env python3
from config import BAUD_RATE, UPDATE_INTERVAL_MS, PLOT_UPDATE_INTERVAL_MS, MAX_POINTS

import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
import serial
import threading

from variables import SENSOR_KEYS
from data import data_history, start_time
from plot import DynamicPlot
from tiles import TilingArea
from uart import select_serial_port, open_serial_port, change_serial_port, get_serial_connection, last_ok_time, start_serial_reader
from logger import *
from focus import FocusManager

# Import 3D Model View functionality
from model import create_3d_model_view, load_model

# Import menu setup
from menu import setup_menu_bar

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
main_layout = QtWidgets.QHBoxLayout(central_widget)
central_widget.setLayout(main_layout)

# --- Left Column: Variables List and CSV Logger ---
left_widget = QtWidgets.QWidget()
left_layout = QtWidgets.QVBoxLayout(left_widget)
left_layout.setContentsMargins(5, 5, 5, 5)
left_layout.setSpacing(5)

variables_list = VariablesList()
variables_list.setFixedHeight(500)
left_layout.addWidget(variables_list)

csv_logger_widget = CSVLoggerWidget()
left_layout.addWidget(csv_logger_widget)

# --- Middle Column: Plot Area (Tiling Area) ---
tiling_area = TilingArea()

# --- Right Column: 3D Model View (Initially Hidden) ---


# --- Toggle Button for 3D Model Visibility ---
def toggle_model_view():
    """Toggle the visibility of the 3D model section."""
    model_view.setVisible(not model_view.isVisible())
    toggle_button.setText("Hide 3D Model" if model_view.isVisible() else "Show 3D Model")

toggle_button = QtWidgets.QPushButton("Show 3D Model")
toggle_button.clicked.connect(toggle_model_view)
left_layout.addWidget(toggle_button)

model_view = create_3d_model_view()
model_item = load_model()
if model_item is not None:
    model_view.addItem(model_item)
else:
    # Disable the toggle button if no model was loaded.
    toggle_button.setEnabled(False)
model_view.setFixedWidth(400)
model_view.setVisible(False)  # Initially hidden


# --- Create Horizontal Splitter ---
main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
main_layout.addWidget(main_splitter)
main_splitter.addWidget(left_widget)
main_splitter.addWidget(tiling_area)
main_splitter.addWidget(model_view)
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
freeze_indicator.setFixedSize(20, 20)
freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")

# OK indicator (now a button to open the serial port selection popup)
ok_indicator = QtWidgets.QPushButton("")
ok_indicator.setFixedSize(20, 20)
ok_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
ok_indicator.setFlat(True)

ok_indicator.clicked.connect(change_serial_port)

# Container for both indicators with some margins.
corner_container = QtWidgets.QWidget()
corner_layout = QtWidgets.QHBoxLayout(corner_container)
corner_layout.setContentsMargins(5, 0, 5, 0)
corner_layout.setSpacing(10)
corner_layout.addWidget(freeze_indicator)
corner_layout.addWidget(ok_indicator)
main_window.menuBar().setCornerWidget(corner_container, QtCore.Qt.Corner.TopRightCorner)

def update():
    """Update model view, log data and refresh indicators (non-blocking)."""
    # If the 3D model view is visible and the required sensor data is available, update it.
    if model_view.isVisible() and data_history['ROL'] and data_history['PIT'] and data_history['YAW']:
        roll = data_history['ROL'][-1][0]
        pitch = data_history['PIT'][-1][0]
        yaw = 0#data_history['YAW'][-1][0]
        model_item.resetTransform()
        model_item.translate(0, 0, 0)
        model_item.rotate(yaw, 0, 0, 1)
        model_item.rotate(pitch, 0, 1, 0)
        model_item.rotate(roll, 1, 0, 0)

    # Log data (every new data point has been appended by the serial thread).
    log_data(data_history)

    # Update indicators
    if get_serial_connection() is None or time.time() - last_ok_time > 1:
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

# Start the serial reader thread
start_serial_reader()

main_window.show()
sys.exit(app.exec())
