import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from config import SENSOR_KEYS
from focus import FocusManager

class DynamicPlot(QtWidgets.QWidget):
    selected_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, tiling_area=None):  # Pass reference to TilingArea
        super().__init__(parent)
        self.tiling_area = tiling_area  # Store reference to TilingArea
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.sensor_keys_assigned = []  # Sensors added to this plot
        self.curves = {}
        self.init_ui()
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px solid gray;")
        self.display_mode = False  # Track the current display mode

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create the PlotWidget for dynamic plotting.
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAcceptDrops(False)
        self.plot.viewport().setAcceptDrops(False)
        self.legend = self.plot.addLegend(offset=(10, 10))
        self.legend.anchor = (0, 0)
        self.layout.addWidget(self.plot)

        # Remove Button inside plot area (floating) to remove the entire plot.
        self.remove_button = QtWidgets.QPushButton("✖")
        self.remove_button.setParent(self)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.move(self.width() - 25, 5)  # Position top-right
        self.remove_button.setStyleSheet(
            "background-color: rgba(255, 0, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.remove_button.clicked.connect(self.remove_self)

        # Toggle Mode Button
        self.toggle_button = QtWidgets.QPushButton("D")
        self.toggle_button.setFixedSize(20, 20)  # Small button size
        self.toggle_button.setStyleSheet(
            "background-color: rgba(0, 255, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.toggle_button.setParent(self)
        self.toggle_button.move(self.width() - 50, 5)  # Position next to remove button

        # Create a container for display mode widgets
        self.display_container = QtWidgets.QWidget(self)
        self.display_layout = QtWidgets.QVBoxLayout(self.display_container)
        self.display_container.hide()  # Initially hidden
        self.layout.addWidget(self.display_container)  # Add display container to the main layout

    def remove_self(self):
        """Safely remove itself from TilingArea."""
        if self.tiling_area:
            self.tiling_area.remove_plot(self)

    def resizeEvent(self, event):
        """Update remove button position when resizing the plot."""
        super().resizeEvent(event)
        self.remove_button.move(self.width() - 25, 5)  # Keep it in top-right corner
        self.toggle_button.move(self.width() - 50, 5)  # Keep it next to remove button

    def add_sensor(self, sensor):
        """Adds a new sensor stream to the plot if not already present."""
        if sensor in self.sensor_keys_assigned:
            return  # Sensor already added.
        
        self.sensor_keys_assigned.append(sensor)
        color = self.get_color(len(self.sensor_keys_assigned) - 1)
        curve = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=sensor)
        self.curves[sensor] = curve
        self.update_legend()

    def remove_sensor(self, sensor):
        """Removes an existing sensor stream from the plot."""
        if sensor in self.sensor_keys_assigned:
            self.sensor_keys_assigned.remove(sensor)
            if sensor in self.curves:
                curve = self.curves.pop(sensor)
                self.plot.removeItem(curve)
            self.update_legend()

    def update_legend(self):
        """Updates the legend based on the current sensor streams."""
        self.legend.clear()
        for sensor in self.sensor_keys_assigned:
            if sensor in self.curves:
                self.legend.addItem(self.curves[sensor], sensor)
    
    def get_color(self, index):
        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 165, 0),
            (128, 0, 128),
            (0, 255, 255),
            (255, 192, 203)
        ]
        return colors[index % len(colors)]
    
    def update_plot(self, data_history):
        for sensor in self.sensor_keys_assigned:
            pts = data_history.get(sensor, [])
            if pts:
                t = np.arange(len(pts))
                self.curves[sensor].setData(t, np.array(pts))

        if self.display_mode:
            self.show_display_mode(data_history)
    
    def mousePressEvent(self, event):
        FocusManager.set_active(self)
        self.selected_signal.emit(self)
        super().mousePressEvent(event)

    def toggle_mode(self):
        """Switch between plot mode and display mode."""
        self.display_mode = not self.display_mode
        if self.display_mode:
            self.toggle_button.setText("P")
            self.plot.hide()  # Hide the plot area
            self.display_container.show()  # Show the display mode container
            
            # Ensure the buttons remain clickable by raising them above the display_container.
            self.remove_button.raise_()
            self.toggle_button.raise_()
            
            self.show_display_mode({})  # Initialize display mode
        else:
            self.toggle_button.setText("D")
            self.plot.show()  # Show the plot area
            self.display_container.hide()  # Hide the display mode container

    def show_display_mode(self, data_history):
        """Displays the most recent values in large, bold text or a 'No data available' message."""
        
        # Clear the current display layout
        self.clear_layout(self.display_layout)

        for sensor in self.sensor_keys_assigned:
            if sensor in data_history and data_history[sensor]:  # Check if there's data for the sensor
                value = data_history[sensor][-1]  # Get most recent value
                label = QtWidgets.QLabel(f"{sensor}: {value:.2f}")
                label.setStyleSheet("font-size: 24px; font-weight: bold;")
            else:
                # If no data exists, show a 'No data available' message
                label = QtWidgets.QLabel(f"{sensor}: No data available")
                label.setStyleSheet("font-size: 24px; font-weight: bold; color: red;")
            
            self.display_layout.addWidget(label)

    def clear_layout(self, layout):
        """Clear all items from the layout."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
    
    def get_state(self):
        """Return the current state of the plot as a dictionary."""
        # Get geometry relative to its parent (x, y, width, height)
        geom = self.geometry().getRect()  # (x, y, width, height)
        return {
            "geometry": {"x": geom[0], "y": geom[1], "width": geom[2], "height": geom[3]},
            "sensor_keys": self.sensor_keys_assigned,
            "display_mode": "display" if self.display_mode else "plot"
        }
