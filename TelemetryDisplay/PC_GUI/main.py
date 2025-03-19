#!/usr/bin/env python3
import sys
import time
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt6 import QtWidgets, QtCore
import serial

from config import SENSOR_KEYS, BAUD_RATE, UPDATE_INTERVAL_MS, MAX_POINTS
from data import data_history
from plot import DynamicPlot
from tiles import TilingArea
from variables import VariablesList
from uart import select_serial_port, open_serial_port
import logger

# --- Application Setup ---
app = QtWidgets.QApplication([])

# --- Serial Port Setup ---
port = select_serial_port()
ser = open_serial_port(port)

main_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout(main_widget)
main_widget.setWindowTitle("e-Tech Sailing Telemetry Logger")
main_widget.resize(1400, 800)

# Top layout: split between plots and cube view.
top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
main_layout.addWidget(top_splitter)

# Left composite widget: variables list and tiling area.
left_composite = QtWidgets.QWidget()
left_layout = QtWidgets.QHBoxLayout(left_composite)
left_layout.setContentsMargins(0, 0, 0, 0)
variables_list = VariablesList()
variables_list.setFixedWidth(150)
left_layout.addWidget(variables_list)
tiling_area = TilingArea()
left_layout.addWidget(tiling_area)
top_splitter.addWidget(left_composite)

# Right pane: Cube view.
cube_view = gl.GLViewWidget()
cube_view.opts['distance'] = 2  # Set viewing distance.
top_splitter.addWidget(cube_view)

# Create a cube mesh.
cube_mesh = gl.MeshData.cylinder(rows=1, cols=4, radius=[0.5, 0.5], length=1.0)
cube_item = gl.GLMeshItem(meshdata=cube_mesh, smooth=False, color=(1, 1, 0, 1),
                            shader='shaded', drawEdges=True)
cube_item.translate(0, 0, -0.5)
cube_view.addItem(cube_item)

# --- Logger Control Panel (Resizable) ---
logger_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)  # Use QSplitter to make it resizable
logger_group = QtWidgets.QGroupBox("CSV Logger")
logger_group.setFixedHeight(100)
logger_layout = QtWidgets.QHBoxLayout(logger_group)

checkbox_widget = QtWidgets.QWidget()
checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
logger_layout.addWidget(checkbox_widget)

log_checkboxes = {}
for sensor in SENSOR_KEYS:
    cb = QtWidgets.QCheckBox(sensor)
    cb.setChecked(True)
    log_checkboxes[sensor] = cb
    checkbox_layout.addWidget(cb)

logger_layout.addStretch()
log_button = QtWidgets.QPushButton("Start Logging")
logger_layout.addWidget(log_button)

# Add logger group inside a splitter for resizing
logger_splitter.addWidget(logger_group)

# Add the logger_splitter to the main layout
main_layout.addWidget(logger_splitter)


log_button.clicked.connect(
    lambda: logger.toggle_logging(log_button, log_checkboxes, SENSOR_KEYS)
)

# --- Update Function ---
def update():
    # Read serial data.
    while ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            continue
        if not line or ':' not in line:
            continue
        key, value_str = line.split(':', 1)
        try:
            value = float(value_str)
        except ValueError:
            continue
        if key in data_history:
            data_history[key].append(value)
            if len(data_history[key]) > MAX_POINTS:
                data_history[key] = data_history[key][-MAX_POINTS:]
    
    # Update plots.
    for plot in tiling_area.plots.keys():
        plot.update_plot(data_history)
    
    # Update cube rotation using latest ROL, PIT, YAW values.
    if data_history['ROL'] and data_history['PIT'] and data_history['YAW']:
        roll  = data_history['ROL'][-1]
        pitch = data_history['PIT'][-1]
        yaw   = data_history['YAW'][-1]
        cube_item.resetTransform()
        cube_item.translate(0, 0, -0.5)
        cube_item.rotate(yaw,   0, 0, 1)
        cube_item.rotate(pitch, 0, 1, 0)
        cube_item.rotate(roll,  1, 0, 0)
    
    # CSV Logging.
    logger.log_data(data_history)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(UPDATE_INTERVAL_MS)

# --- Connect Variables List Interaction ---
def add_variable_to_selected(item):
    if tiling_area.selected_plot is not None:
        tiling_area.selected_plot.add_sensor(item.text())

variables_list.itemDoubleClicked.connect(add_variable_to_selected)

# Ensure at least one plot exists.
tiling_area.add_initial_row()

main_widget.show()
sys.exit(app.exec())
