#!/usr/bin/env python3
import sys
import serial
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtWidgets, QtCore

# --- Configuration ---
SERIAL_PORT = '/dev/ttyUSB0'  # Change as needed (e.g., 'COM3' on Windows)
BAUD_RATE = 115200
UPDATE_INTERVAL_MS = 25      # Update interval (ms)
MAX_POINTS = 500             # Maximum data points to store per channel

# Sensor keys we care about:
# 2D plots: accel (ACX, ACY, ACZ), gyro (GYX, GYY, GYZ), mag (MGX, MGY, MGZ)
# Cube rotation: ROL, PIT, YAW
sensor_keys = ['ACX', 'ACY', 'ACZ',
               'GYX', 'GYY', 'GYZ',
               'MGX', 'MGY', 'MGZ',
               'ROL', 'PIT', 'YAW']

# Define sensor groups for 2D plots
groups = {
    'accel': ['ACX', 'ACY', 'ACZ'],
    'gyro':  ['GYX', 'GYY', 'GYZ'],
    'mag':   ['MGX', 'MGY', 'MGZ']
}

# --- Data Storage ---
# We keep a history for each sensor key.
data_history = {key: [] for key in sensor_keys}
time_history = []  # Global time/sample index

# --- Initialize Serial Port ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
except serial.SerialException as e:
    sys.exit(f"Error opening serial port {SERIAL_PORT}: {e}")

# --- Setup Application and Layout ---
app = QtWidgets.QApplication([])

# Create a main widget with a horizontal layout:
# Left pane: a GraphicsLayoutWidget with 3 2D plots (one per sensor group)
# Right pane: an OpenGL view for the rotating cube.
main_widget = QtWidgets.QWidget()
main_layout = QtWidgets.QHBoxLayout(main_widget)
main_widget.setWindowTitle("IMU 2D & 3D Visualization")
main_widget.resize(1400, 800)

# --- Left Pane: 2D Plots ---
plot_widget = pg.GraphicsLayoutWidget()
plot_widget.setBackground('w')
main_layout.addWidget(plot_widget, 1)  # stretch factor 1

# Create one plot per sensor group and add curves for x, y, z.
plots = {}
curves = {}  # Will hold curves as: { group: {channel: curve} }
colors = {'x': (255, 0, 0), 'y': (0, 255, 0), 'z': (0, 0, 255)}

for group_name, keys in groups.items():
    p = plot_widget.addPlot(title=f"{group_name.capitalize()} (XYZ)", row=None, col=0)
    p.showGrid(x=True, y=True)
    group_curves = {}
    group_curves[keys[0]] = p.plot(pen=pg.mkPen(color=colors['x'], width=2), name=keys[0])
    group_curves[keys[1]] = p.plot(pen=pg.mkPen(color=colors['y'], width=2), name=keys[1])
    group_curves[keys[2]] = p.plot(pen=pg.mkPen(color=colors['z'], width=2), name=keys[2])
    curves[group_name] = group_curves
    plot_widget.nextRow()

# --- Right Pane: OpenGL Cube View ---
cube_view = gl.GLViewWidget()
cube_view.opts['distance'] = 40  # set viewing distance
main_layout.addWidget(cube_view, 1)

# Create a "cube" mesh.
# Since MeshData has no cube() method, we use the cylinder method with 4 sides.
cube_mesh = gl.MeshData.cylinder(rows=1, cols=4, radius=[0.5, 0.5], length=1.0)
cube_item = gl.GLMeshItem(meshdata=cube_mesh, smooth=False, color=(1, 1, 0, 1),
                            shader='shaded', drawEdges=True)
# Translate the cube so it's centered at the origin.
cube_item.translate(0, 0, -0.5)
cube_view.addItem(cube_item)

# --- Update Function ---
def update():
    global time_history
    # Read serial data, line by line.
    while ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            continue  # Skip lines that can't be decoded
        if not line or ':' not in line:
            continue
        key, value_str = line.split(':', 1)
        try:
            value = float(value_str)
        except ValueError:
            continue  # Skip non-numeric values
        if key in data_history:
            data_history[key].append(value)
            if len(data_history[key]) > MAX_POINTS:
                data_history[key] = data_history[key][-MAX_POINTS:]
    
    # Update the global time history using the maximum number of samples available.
    if any(len(data_history[k]) for k in sensor_keys):
        n_points = max(len(data_history[k]) for k in sensor_keys)
        time_history = list(range(n_points))
    
    # Update 2D plots for each sensor group.
    for group_name, keys in groups.items():
        for key in keys:
            if data_history[key]:
                pts = data_history[key][-len(time_history):]
                curves[group_name][key].setData(time_history[-len(pts):], pts)
    
    # Update cube rotation using the latest ROL, PIT, YAW values.
    if data_history['ROL'] and data_history['PIT'] and data_history['YAW']:
        roll  = data_history['ROL'][-1]
        pitch = data_history['PIT'][-1]
        yaw   = data_history['YAW'][-1]
        cube_item.resetTransform()
        cube_item.translate(0, 0, -0.5)
        # Rotate: apply yaw (around Z), then pitch (around Y), then roll (around X)
        cube_item.rotate(yaw,   0, 0, 1)
        cube_item.rotate(pitch, 0, 1, 0)
        cube_item.rotate(roll,  1, 0, 0)

# --- Timer for Updating ---
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(UPDATE_INTERVAL_MS)

# --- Start the Application ---
main_widget.show()
sys.exit(app.exec_())
