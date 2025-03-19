import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from config import SENSOR_KEYS
from focus import FocusManager

class DynamicPlot(QtWidgets.QWidget):
    # Signal to notify selection.
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
        self.remove_button.setParent(self.plot)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.move(self.plot.width() - 25, 5)  # Position top-right
        self.remove_button.setStyleSheet(
            "background-color: rgba(255, 0, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.remove_button.clicked.connect(self.remove_self)
    
    def remove_self(self):
        """Safely remove itself from TilingArea."""
        if self.tiling_area:
            self.tiling_area.remove_plot(self)

    def resizeEvent(self, event):
        """Update remove button position when resizing the plot."""
        super().resizeEvent(event)
        self.remove_button.move(self.plot.width() - 25, 5)  # Keep it in top-right corner

    def add_sensor(self, sensor):
        """Adds a new sensor stream to the plot if not already present."""
        if sensor in self.sensor_keys_assigned:
            return  # Sensor already added.
        self.sensor_keys_assigned.append(sensor)
        color = self.get_color(len(self.sensor_keys_assigned) - 1)
        curve = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=sensor)
        self.curves[sensor] = curve
    
    def remove_sensor(self, sensor):
        """Removes an existing sensor stream from the plot."""
        if sensor in self.sensor_keys_assigned:
            self.sensor_keys_assigned.remove(sensor)
            if sensor in self.curves:
                curve = self.curves.pop(sensor)
                self.plot.removeItem(curve)
            # Rebuild legend to reflect removal.
            self.rebuild_legend()

    def rebuild_legend(self):
        """Rebuilds the legend based on the current sensor streams."""
        # Remove the current legend.
        self.plot.removeItem(self.legend)
        # Create a new legend.
        self.legend = self.plot.addLegend(offset=(10, 10))
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
    
    def mousePressEvent(self, event):
        FocusManager.set_active(self)
        self.selected_signal.emit(self)
        super().mousePressEvent(event)
