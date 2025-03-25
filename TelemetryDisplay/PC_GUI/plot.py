import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from variables import *         # Expects functions like get_sensor_name and get_sensor_direction
from focus import FocusManager  # Expects a FocusManager class
from uart import send_sensor
from data import data_history, start_time
import time

class DynamicPlot(QtWidgets.QWidget):
    selected_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, tiling_area=None):  
        super().__init__(parent)
        self.tiling_area = tiling_area  
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.sensor_keys_assigned = []  
        self.curves = {}
        self.init_ui()
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px solid gray;")
        self.display_mode = False  # Track the current display mode

        # Persistent widgets for display mode:
        # For TX sensors, a container with a sensor name label and an editable QLineEdit.
        self.tx_widgets = {}
        # For RX sensors, a container with a sensor name label and a read-only QLineEdit.
        self.rx_widgets = {}
        # To store the last sent value for TX sensors.
        self.last_tx_values = {}

        self.sensor_colors = {}  # New dictionary to map sensor to color.

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create the plot widget with grid and legend.
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAcceptDrops(False)
        self.plot.viewport().setAcceptDrops(False)
        self.legend = self.plot.addLegend(offset=(10, 10))
        self.legend.anchor = (0, 0)
        self.layout.addWidget(self.plot)

        # Create a QLineEdit to input time window (in seconds) inside the plot.
        self.time_window_edit = QtWidgets.QLineEdit(self.plot)
        self.time_window_edit.setPlaceholderText("Time Window (s)")
        self.time_window_edit.setFixedWidth(100)
        self.time_window_edit.setStyleSheet(
            "background-color: rgba(200, 200, 200, 150); border: 1px solid gray; border-radius: 5px;"
        )
        # Position it at the top left (you can adjust this as needed)
        self.time_window_edit.move(10, 5)
        # Optional: update the range when the user finishes editing.
        self.time_window_edit.editingFinished.connect(self.update_plot)

        # Remove button.
        self.remove_button = QtWidgets.QPushButton("✖")
        self.remove_button.setParent(self)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.move(self.width() - 25, 5)
        self.remove_button.setStyleSheet(
            "background-color: rgba(255, 0, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.remove_button.clicked.connect(self.remove_self)

        # Toggle mode button.
        self.toggle_button = QtWidgets.QPushButton("D")
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.setStyleSheet(
            "background-color: rgba(0, 255, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.toggle_button.setParent(self)
        self.toggle_button.move(self.width() - 50, 5)

        # Container for display mode widgets.
        self.display_container = QtWidgets.QWidget(self)
        self.display_layout = QtWidgets.QVBoxLayout(self.display_container)
        self.display_container.hide()  
        self.layout.addWidget(self.display_container)

    def remove_self(self):
        """Safely remove itself from TilingArea."""
        if self.tiling_area:
            self.tiling_area.remove_plot(self)

    def resizeEvent(self, event):
        """Update remove and toggle button positions when resizing the plot."""
        super().resizeEvent(event)
        self.remove_button.move(self.width() - 25, 5)
        self.toggle_button.move(self.width() - 50, 5)

    def add_sensor(self, sensor):
        """Adds a new sensor stream to the plot if not already present."""
        if sensor in self.sensor_keys_assigned:
            return  
        
        self.sensor_keys_assigned.append(sensor)
        color = self.get_color(sensor)
        curve = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=sensor)
        self.curves[sensor] = curve
        self.update_legend()

        # If in display mode, add the corresponding display widget.
        if self.display_mode:
            self.add_display_widget(sensor)

    def add_display_widget(self, sensor):
        """Add a display widget for a newly added sensor based on its direction."""
        if get_sensor_direction(sensor) == 'TX':
            if sensor not in self.tx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")  # Remove borders for clean UI
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(get_sensor_name(sensor) + ": ")
                name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                editable_input = QtWidgets.QLineEdit()
                editable_input.setPlaceholderText(f"Enter {sensor} value...")
                editable_input.setStyleSheet("font-size: 24px; font-weight: bold;")
                editable_input.returnPressed.connect(
                    lambda sensor=sensor, input_field=editable_input: self.on_return_pressed(sensor, input_field)
                )
                h_layout.addWidget(editable_input)
                self.tx_widgets[sensor] = (container, name_label, editable_input)
                self.display_layout.addWidget(container)
        else:
            if sensor not in self.rx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")  # Remove borders for clean UI
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(get_sensor_name(sensor) + ": ")
                name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                output_field = QtWidgets.QLineEdit()
                output_field.setReadOnly(True)
                output_field.setStyleSheet("font-size: 24px; font-weight: bold;")
                h_layout.addWidget(output_field)
                self.rx_widgets[sensor] = (container, name_label, output_field)
                self.display_layout.addWidget(container)


    def remove_sensor(self, sensor):
        """Removes an existing sensor stream from the plot."""
        if sensor in self.sensor_keys_assigned:
            self.sensor_keys_assigned.remove(sensor)
            if sensor in self.curves:
                curve = self.curves.pop(sensor)
                self.plot.removeItem(curve)
            self.update_legend()

            # Remove display widgets.
            if sensor in self.tx_widgets:
                widget = self.tx_widgets.pop(sensor)[0]
                widget.deleteLater()
            if sensor in self.rx_widgets:
                widget = self.rx_widgets.pop(sensor)[0]
                widget.deleteLater()

    def update_legend(self):
        """Updates the legend based on the current sensor streams."""
        self.legend.clear()
        for sensor in self.sensor_keys_assigned:
            if sensor in self.curves:
                self.legend.addItem(self.curves[sensor], get_sensor_name(sensor))
    

    def get_color(self, sensor):
        """Return a color for the sensor. If not assigned, generate and store a new color."""
        if sensor in self.sensor_colors:
            return self.sensor_colors[sensor]

        # Predefined base colors for initial sensors
        base_colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 165, 0),
            (128, 0, 128),
            (0, 255, 255),
            (255, 192, 203)
        ]

        if len(self.sensor_colors) < len(base_colors):
            new_color = base_colors[len(self.sensor_colors)]
        else:
            # Generate a new color dynamically using HSV
            hue = (len(self.sensor_colors) * 37) % 360  # Spread colors around the hue wheel
            hsv_color = pg.hsvColor(hue / 360.0, 1.0, 1.0)  # Normalize hue to [0,1]
            new_color = hsv_color.getRgb()[:3]  # Extract RGB tuple

        self.sensor_colors[sensor] = new_color
        return new_color

        
    def update_plot(self, data_history=data_history):
        # Update plot curves.
        current_time = time.time() - start_time
        for sensor in self.sensor_keys_assigned:
            if sensor in data_history and len(data_history[sensor]) > 0:
                # Extract the last timestamp and value from the history
                last_value = data_history[sensor][-1][0]
                last_timestamp = data_history[sensor][-1][1]

                # Get the current timestamp and append value if needed
                if current_time - last_timestamp >= 0.5:  # 500ms
                    data_history[sensor].append((last_value, current_time))

                # Extract time and data for plotting
                times = [entry[1] for entry in data_history[sensor]]
                values = [entry[0] for entry in data_history[sensor]]

                # Update the plot data for this sensor
                self.curves[sensor].setData(times, values)

        # Apply time window if specified.
        try:
            time_window = float(self.time_window_edit.text())
        except ValueError:
            time_window = 0

        if time_window > 0:
            # Force the x-axis to show only the last 'time_window' seconds.
            self.plot.setXRange(max(0, current_time - time_window), current_time)
        else:
            # If time window is 0 (or invalid), auto-range to show all data.
            self.plot.enableAutoRange(axis='x')

        # In display mode, update the display widgets.
        if self.display_mode:
            self.update_display_widgets(data_history)
        
    def mousePressEvent(self, event):
        FocusManager.set_active(self)
        self.selected_signal.emit(self)
        super().mousePressEvent(event)

    def toggle_mode(self):
        """Switch between plot mode and display mode."""
        self.display_mode = not self.display_mode
        if self.display_mode:
            self.toggle_button.setText("P")
            self.plot.hide()
            self.display_container.show()  
            self.remove_button.raise_()
            self.toggle_button.raise_()
            self.populate_display_mode()
        else:
            self.toggle_button.setText("D")
            self.plot.show()
            self.display_container.hide()  

    def populate_display_mode(self):
        """(Re)populate the display layout with persistent widgets for each sensor."""
        # Clear the layout without deleting our persistent widgets.
        while self.display_layout.count():
            item = self.display_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for sensor in self.sensor_keys_assigned:
            if get_sensor_direction(sensor) == 'TX':
                if sensor not in self.tx_widgets:
                    self.add_display_widget(sensor)
                else:
                    self.display_layout.addWidget(self.tx_widgets[sensor][0])
            else:
                if sensor not in self.rx_widgets:
                    self.add_display_widget(sensor)
                else:
                    self.display_layout.addWidget(self.rx_widgets[sensor][0])
        
        # Update displayed text immediately.
        self.update_display_widgets({})

    def update_display_widgets(self, data_history):
        """Update display widget text.
           For TX sensors, if a last sent value exists, show it;
           otherwise, if data is available, show that value.
           For RX sensors, update the read-only field with the latest data.
           TX updates occur only if the field is not focused.
        """
        for sensor in self.sensor_keys_assigned:
            value = None
            if sensor in data_history and data_history[sensor]:
                value = data_history[sensor][-1][0]
            
            if get_sensor_direction(sensor) == 'TX':
                # Prioritize the last sent value.
                current_value = self.last_tx_values.get(sensor, value)
                container, name_label, input_field = self.tx_widgets[sensor]
                if not input_field.hasFocus():
                    input_field.setText(str(current_value) if current_value is not None else "")
            else:
                # RX sensors: update the read-only QLineEdit.
                container, name_label, output_field = self.rx_widgets[sensor]
                if value is not None:
                    output_field.setText(str(value))
                else:
                    output_field.setText("No data available")

    def on_return_pressed(self, sensor, input_field):
        """Handles Enter key press: converts text to float, stores it, updates data_history, and flashes the background."""
        try:
            new_value = float(input_field.text())
        except ValueError:
            return  # Ignore invalid input

        send_sensor(sensor, new_value)

        # Update the data history.
        if sensor not in data_history:
            data_history[sensor] = []
        data_history[sensor].append((new_value, time.time() - start_time))

        # Store the last sent value.
        self.last_tx_values[sensor] = new_value

        # Flash the background of the input field to green for confirmation.
        input_field.setStyleSheet("background-color: green; font-size: 24px; font-weight: bold;")
        QtCore.QTimer.singleShot(150, lambda: input_field.setStyleSheet("font-size: 24px; font-weight: bold;"))

        print(f"Updated {sensor} with value: {new_value}")

    def clear_layout(self, layout):
        """Clear all items from the layout."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def get_state(self):
        """Return the current state of the plot as a dictionary."""
        geom = self.geometry().getRect()
        return {
            "geometry": {"x": geom[0], "y": geom[1], "width": geom[2], "height": geom[3]},
            "sensor_keys": self.sensor_keys_assigned,
            "display_mode": "display" if self.display_mode else "plot"
        }
