#!/usr/bin/env python3
import sys
import csv
import time
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt6 import QtWidgets, QtCore
import serial

from config import SENSOR_KEYS, BAUD_RATE, UPDATE_INTERVAL_MS, MAX_POINTS, MODEL_PATH
from data import data_history
from plot import DynamicPlot
from tiles import TilingArea
from uart import select_serial_port, open_serial_port
from logger import *
from focus import FocusManager

# Import the necessary libraries for loading STL and OBJ files
from stl import mesh as stlMesh
import trimesh

# --- Global Logging Variables ---
logging_active = False
logging_start_time = None
logging_vars = []  # Captured sensor keys for logging when logging starts.
csv_file = None
csv_writer = None

# --- Application Setup ---
app = QtWidgets.QApplication([])

# --- Serial Port Setup ---
port = select_serial_port()
ser = open_serial_port(port)

main_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QHBoxLayout(main_widget)  # We'll use a horizontal layout for the three columns.
main_widget.setWindowTitle("e-Tech Sailing Telemetry Logger")
main_widget.resize(1400, 800)

# Create a horizontal splitter to hold three columns.
main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
main_layout.addWidget(main_splitter)

# --- Left Column: Variables List and CSV Logger ---
left_widget = QtWidgets.QWidget()
left_layout = QtWidgets.QVBoxLayout(left_widget)
left_layout.setContentsMargins(5, 5, 5, 5)
left_layout.setSpacing(5)

variables_list = VariablesList()
# Optionally, you can set a fixed height for the variables list.
variables_list.setFixedHeight(500)
left_layout.addWidget(variables_list)

csv_logger_widget = CSVLoggerWidget()
left_layout.addWidget(csv_logger_widget)

# --- Middle Column: Plot Area (Tiling Area) ---
tiling_area = TilingArea()

# --- Right Column: 3D Model View ---
model_view = gl.GLViewWidget()
model_view.opts['distance'] = 2  # Set viewing distance.
model_view.setBackgroundColor('w')  # White background.


# After creating model_view and tiling_area:
model_view.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
tiling_area.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)

# Add the three columns to the splitter.
main_splitter.addWidget(left_widget)
main_splitter.addWidget(tiling_area)
main_splitter.addWidget(model_view)
# Optionally, set stretch factors.
main_splitter.setStretchFactor(0, 1)
main_splitter.setStretchFactor(1, 3)
main_splitter.setStretchFactor(2, 1)

# --- Load Model (STL or OBJ) ---
def load_model(file_path):
    if file_path.lower().endswith('.stl'):
        stl_model = stlMesh.Mesh.from_file(file_path)
        verts = stl_model.vectors.reshape(-1, 3)
        num_triangles = stl_model.vectors.shape[0]
        faces = np.arange(num_triangles * 3).reshape(-1, 3)
        model_meshdata = gl.MeshData(vertexes=verts, faces=faces)
    elif file_path.lower().endswith('.obj'):
        obj_model = trimesh.load_mesh(file_path)
        verts = obj_model.vertices
        faces = obj_model.faces
        model_meshdata = gl.MeshData(vertexes=verts, faces=faces)
    else:
        raise ValueError("Unsupported file format. Please use STL or OBJ.")
    
    model_item = gl.GLMeshItem(
        meshdata=model_meshdata,
        smooth=True,
        color=(1, 1, 0, 1),
        shader='shaded',
        glOptions='opaque',
        drawEdges=False
    )
    model_item.translate(0, 0, 0)
    return model_item

model_item = load_model(MODEL_PATH)  # Update MODEL_PATH accordingly.
model_view.addItem(model_item)

# --- Connect CSV Logger Button ---
csv_logger_widget.log_button.clicked.connect(
    lambda: toggle_logging(csv_logger_widget)
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
    
    # Update model rotation using latest ROL, PIT, YAW values.
    if data_history['ROL'] and data_history['PIT'] and data_history['YAW']:
        roll  = data_history['ROL'][-1]
        pitch = data_history['PIT'][-1]
        yaw   = data_history['YAW'][-1]
        model_item.resetTransform()
        model_item.translate(0, 0, 0)
        model_item.rotate(yaw,   0, 0, 1)
        model_item.rotate(pitch, 0, 1, 0)
        model_item.rotate(roll,  1, 0, 0)
    
    # CSV Logging.
    log_data(data_history)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(UPDATE_INTERVAL_MS)


def add_variable_to_selected(item):
    sensor = item.text()
    active_widget = FocusManager.get_active()
    if active_widget is None:
        return
    if isinstance(active_widget, CSVLoggerWidget):
        active_widget.toggle_sensor(sensor)
    else:
        # Assume it's a DynamicPlot; add sensor if not already present.
        if sensor not in active_widget.sensor_keys_assigned:
            active_widget.add_sensor(sensor)
        else:
            active_widget.remove_sensor(sensor)

variables_list.itemDoubleClicked.connect(add_variable_to_selected)

# Ensure at least one plot exists.
tiling_area.add_initial_row()

main_widget.show()
sys.exit(app.exec())
