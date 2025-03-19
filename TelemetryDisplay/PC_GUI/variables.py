from PyQt6 import QtWidgets, QtCore
from config import SENSOR_KEYS

class VariablesList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        for sensor in SENSOR_KEYS:
            item = QtWidgets.QListWidgetItem(sensor)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
            self.addItem(item)
