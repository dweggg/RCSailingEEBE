#!/usr/bin/env python3
import os, sys, math, time, csv
import serial
from serial.tools import list_ports
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtWidgets, QtCore

# --- Set Qt Platform Based on OS ---
if sys.platform.startswith('linux'):
    # For Linux, check if running under Wayland or fall back to X11 (xcb)
    if "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland"
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
# On Windows, nothing extra is needed.

# --- Configuration ---
BAUD_RATE = 115200
UPDATE_INTERVAL_MS = 25      # Update interval in ms
MAX_POINTS = 500             # Maximum data points to store per channel

# Sensor keys:
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
data_history = {key: [] for key in sensor_keys}
time_history = []  # Global time/sample index

# --- Global variables for CSV Logging ---
logging_active = False
logging_start_time = None
logging_vars = []  # List of sensor keys to log (set when logging starts)
csv_file = None
csv_writer = None

# --- Create Application ---
app = QtWidgets.QApplication([])

# --- Graphical Serial Port Selector ---
ports = [port.device for port in list_ports.comports()]
if not ports:
    sys.exit("No serial ports found.")

port, ok = QtWidgets.QInputDialog.getItem(None, "Select Serial Port",
                                            "Serial Port:", ports, 0, False)
if not ok:
    sys.exit("No serial port selected.")

try:
    ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
except serial.SerialException as e:
    sys.exit(f"Error opening serial port {port}: {e}")

# --- Setup Main Application Layout ---
# Use a vertical layout: top part is the plots & cube, bottom part is the logger controls.
main_widget = QtWidgets.QWidget()
main_vlayout = QtWidgets.QVBoxLayout(main_widget)
main_widget.setWindowTitle("e-Tech Sailing IMU logger")
main_widget.resize(1400, 800)

# Top layout: horizontal split between plots and cube view.
top_layout = QtWidgets.QHBoxLayout()
main_vlayout.addLayout(top_layout)

# --- Left Pane: 2D Plots ---
plot_widget = pg.GraphicsLayoutWidget()
plot_widget.setBackground('w')
top_layout.addWidget(plot_widget, 1)  # stretch factor 1

curves = {}
colors = {'x': (255, 0, 0), 'y': (0, 255, 0), 'z': (0, 0, 255)}
for group_name, keys in groups.items():
    p = plot_widget.addPlot(title=f"{group_name.capitalize()} (XYZ)")
    p.showGrid(x=True, y=True)
    group_curves = {}
    group_curves[keys[0]] = p.plot(pen=pg.mkPen(color=colors['x'], width=2))
    group_curves[keys[1]] = p.plot(pen=pg.mkPen(color=colors['y'], width=2))
    group_curves[keys[2]] = p.plot(pen=pg.mkPen(color=colors['z'], width=2))
    curves[group_name] = group_curves
    plot_widget.nextRow()

# --- Right Pane: OpenGL Cube View ---
cube_view = gl.GLViewWidget()
cube_view.opts['distance'] = 2  # Set viewing distance
top_layout.addWidget(cube_view, 1)

# Create a "cube" mesh.
# (Since MeshData has no cube() method, we use a 4-sided cylinder.)
cube_mesh = gl.MeshData.cylinder(rows=1, cols=4, radius=[0.5, 0.5], length=1.0)
cube_item = gl.GLMeshItem(meshdata=cube_mesh, smooth=False, color=(1, 1, 0, 1),
                            shader='shaded', drawEdges=True)
cube_item.translate(0, 0, -0.5)  # Center the cube at the origin.
cube_view.addItem(cube_item)

# --- Logger Control Panel ---
logger_group = QtWidgets.QGroupBox("CSV Logger")
logger_layout = QtWidgets.QHBoxLayout(logger_group)

# Create a sub-widget with a grid layout for checkboxes.
checkbox_widget = QtWidgets.QWidget()
checkbox_layout = QtWidgets.QGridLayout(checkbox_widget)
logger_layout.addWidget(checkbox_widget)

# Dictionary to store the checkboxes for each sensor.
log_checkboxes = {}
for i, sensor in enumerate(sensor_keys):
    cb = QtWidgets.QCheckBox(sensor)
    cb.setChecked(True)  # default: all sensors logged
    log_checkboxes[sensor] = cb
    checkbox_layout.addWidget(cb, i // 6, i % 6)

# Add a spacer and then a Start/Stop Logging button.
logger_layout.addStretch()
log_button = QtWidgets.QPushButton("Start Logging")
logger_layout.addWidget(log_button)

main_vlayout.addWidget(logger_group)

# --- Logging Toggle Function ---
def toggle_logging():
    global logging_active, logging_start_time, logging_vars, csv_file, csv_writer
    if not logging_active:
        # Start logging.
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save CSV Log", "", "CSV Files (*.csv)")
        if not fname:
            return  # User cancelled.
        try:
            csv_file = open(fname, 'w', newline='')
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Could not open file:\n{e}")
            return
        csv_writer = csv.writer(csv_file)
        # Get list of sensors to log (from the checkboxes).
        logging_vars = [sensor for sensor in sensor_keys if log_checkboxes[sensor].isChecked()]
        header = ["t"] + logging_vars
        csv_writer.writerow(header)
        csv_file.flush()
        logging_start_time = time.time()
        logging_active = True
        log_button.setText("Stop Logging")
    else:
        # Stop logging.
        logging_active = False
        if csv_file:
            csv_file.close()
        log_button.setText("Start Logging")

log_button.clicked.connect(toggle_logging)

# --- Update Function ---
def update():
    global time_history
    # Read serial data line by line.
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
        cube_item.rotate(yaw,   0, 0, 1)
        cube_item.rotate(pitch, 0, 1, 0)
        cube_item.rotate(roll,  1, 0, 0)
    
    # If logging is active, write a new row to the CSV log.
    if logging_active and logging_vars and csv_writer:
        t_ms = (time.time() - logging_start_time)  # elapsed time in s
        # For each sensor to log, take the most recent value if available.
        row = [t_ms]
        for sensor in logging_vars:
            if data_history[sensor]:
                row.append(data_history[sensor][-1])
            else:
                row.append("")
        csv_writer.writerow(row)
        csv_file.flush()

# --- Timer for Updates ---
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(UPDATE_INTERVAL_MS)

# --- Start the Application ---
main_widget.show()
sys.exit(app.exec_())
