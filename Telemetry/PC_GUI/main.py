#!/usr/bin/env python3
import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
import serial

from config import BAUD_RATE, UPDATE_INTERVAL_MS, MAX_POINTS, MODEL_PATH
from variables import SENSOR_KEYS
from data import data_history, start_time
from plot import DynamicPlot
from tiles import TilingArea
from uart import select_serial_port, open_serial_port
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

# Global timestamp for the last received OK message.
last_ok_time = 0

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
model_view = create_3d_model_view()
model_item = load_model(MODEL_PATH)
model_view.addItem(model_item)
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

# --- Toggle Button for 3D Model Visibility ---
def toggle_model_view():
    """Toggle the visibility of the 3D model section."""
    model_view.setVisible(not model_view.isVisible())
    toggle_button.setText("Hide 3D Model" if model_view.isVisible() else "Show 3D Model")

toggle_button = QtWidgets.QPushButton("Show 3D Model")
toggle_button.clicked.connect(toggle_model_view)
left_layout.addWidget(toggle_button)

# --- Connect CSV Logger Button ---
csv_logger_widget.log_button.clicked.connect(lambda: toggle_logging(csv_logger_widget))

# --- Setup Menu Bar (called only once) ---
setup_menu_bar(main_window, tiling_area)

# --- Create Indicators in Menu Bar Corner ---
# Freeze indicator (shows pause status)
freeze_indicator = QtWidgets.QLabel()
freeze_indicator.setFixedSize(20, 20)
# Initial style: not paused (light gray)
freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")

# OK indicator (shows serial connection status)
ok_indicator = QtWidgets.QLabel()
ok_indicator.setFixedSize(20, 20)
ok_indicator.setStyleSheet("background-color: red; border-radius: 10px;")

# Container for both indicators with some margins.
corner_container = QtWidgets.QWidget()
corner_layout = QtWidgets.QHBoxLayout(corner_container)
corner_layout.setContentsMargins(5, 0, 5, 0)  # Adjust margins as needed
corner_layout.setSpacing(10)
# Add freeze indicator first, then OK indicator.
corner_layout.addWidget(freeze_indicator)
corner_layout.addWidget(ok_indicator)
main_window.menuBar().setCornerWidget(corner_container, QtCore.Qt.Corner.TopRightCorner)

# --- Serial Port Setup ---
port = select_serial_port()
ser = open_serial_port(port)

# --- Update Function ---
def update():
    """Fetch serial data, update plots, rotate the 3D model (if visible) and update indicators."""
    global last_ok_time

    if not freeze_plots:
        try:
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').strip()
                except UnicodeDecodeError:
                    continue
                # Check for the "OK" message and update timestamp
                if line == "OK":
                    last_ok_time = time.time()
                # Process sensor data lines in "KEY:VALUE" format
                if not line or ':' not in line:
                    continue
                key, value_str = line.split(':', 1)
                try:
                    value = float(value_str)
                except ValueError:
                    continue
                if key in data_history:
                    data_history[key].append((value, time.time() - start_time))
                    if len(data_history[key]) > MAX_POINTS:
                        data_history[key] = data_history[key][-MAX_POINTS:]
        except OSError as e:
            print("Serial port error:", e)
            # Optionally, you can implement a reconnection strategy here.
    
        # Update plots
        for plot in tiling_area.plots.keys():
            plot.update_plot(data_history)
    
        # Update 3D model rotation only if visible and sensor data available
        if model_view.isVisible() and data_history['ROL'] and data_history['PIT'] and data_history['YAW']:
            roll = data_history['ROL'][-1][0]
            pitch = data_history['PIT'][-1][0]
            yaw = data_history['YAW'][-1][0]
            model_item.resetTransform()
            model_item.translate(0, 0, 0)
            model_item.rotate(yaw, 0, 0, 1)
            model_item.rotate(pitch, 0, 1, 0)
            model_item.rotate(roll, 1, 0, 0)
    
        # CSV Logging
        log_data(data_history)

    # Update the OK connection indicator regardless of freeze state.
    if time.time() - last_ok_time > 1:
        ok_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
    else:
        ok_indicator.setStyleSheet("background-color: green; border-radius: 10px;")
    
    # Update the freeze indicator based on the freeze_plots flag.
    if freeze_plots:
        freeze_indicator.setStyleSheet("background-color: blue; border-radius: 10px;")
    else:
        freeze_indicator.setStyleSheet("background-color: lightgray; border-radius: 10px;")

# --- Timer for Updates ---
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(UPDATE_INTERVAL_MS)

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

# Ensure at least one plot exists
tiling_area.add_initial_row()

# --- Override KeyPressEvent in Main Window for Spacebar Freeze ---
original_keyPressEvent = main_window.keyPressEvent
def custom_keyPressEvent(event):
    global freeze_plots
    if event.key() == QtCore.Qt.Key.Key_Space:
        freeze_plots = not freeze_plots
    else:
        original_keyPressEvent(event)
main_window.keyPressEvent = custom_keyPressEvent

main_window.show()
sys.exit(app.exec())
