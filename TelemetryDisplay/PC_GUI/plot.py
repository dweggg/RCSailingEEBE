import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from config import SENSOR_KEYS

class DynamicPlot(QtWidgets.QWidget):
    # Signal to notify selection.
    selected_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # Toolbar with an individual remove button.
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        self.remove_button = QtWidgets.QPushButton("Remove Plot")
        self.remove_button.setMaximumWidth(100)
        toolbar.addWidget(self.remove_button)
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        
        # Create the PlotWidget for dynamic plotting.
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAcceptDrops(False)
        self.plot.viewport().setAcceptDrops(False)
        self.legend = self.plot.addLegend(offset=(10, 10))
        self.legend.anchor = (0, 0)
        self.layout.addWidget(self.plot)
    
    def add_sensor(self, sensor):
        if sensor in self.sensor_keys_assigned:
            return  # Sensor already added.
        self.sensor_keys_assigned.append(sensor)
        color = self.get_color(len(self.sensor_keys_assigned) - 1)
        curve = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=sensor)
        self.curves[sensor] = curve
    
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
        # Temporarily block the layout resizing.
        self.setUpdatesEnabled(False)
        
        try:
            # Emit the signal when clicked.
            self.selected_signal.emit(self)
        finally:
            # Re-enable updates to avoid blocking further updates.
            self.setUpdatesEnabled(True)

        # No call to super().mousePressEvent(event) to prevent unwanted behavior.
