import csv
import time
from PyQt6 import QtWidgets, QtCore
from variables import VariablesList
from focus import FocusManager

# Global logging variables (shared with data.py if needed)
logging_active = False
logging_start_time = None
logging_vars = []  # List of sensor keys to log
csv_file = None
csv_writer = None

# --- CSV Logger Widget ---
class CSVLoggerWidget(QtWidgets.QGroupBox):
    def __init__(self, title="CSV Logger", parent=None):
        super().__init__(title, parent)
        self.selected = False  # Determines if this widget is "active"
        # Allow the widget to gain focus when clicked.
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.init_ui()
    
    def init_ui(self):
        # Change to QVBoxLayout for vertical stacking
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Instead of checkboxes, we use a QListWidget to show selected sensors.
        self.sensor_list_widget = QtWidgets.QListWidget()
        self.sensor_list_widget.setFixedHeight(200)  # Height for the list of selected sensors   
        self.layout.addWidget(self.sensor_list_widget)
        
        # The log button is now placed below the sensor list.
        self.log_button = QtWidgets.QPushButton("Start Logging")
        self.layout.addWidget(self.log_button)
        
        # Start with a gray border for the group box.
        self.setStyleSheet("QGroupBox { border: 2px solid gray; }")

    def mousePressEvent(self, event):
        FocusManager.set_active(self)
        super().mousePressEvent(event)

        
    def isChildOf(self, widget):
        """Helper function to check if the widget is inside this widget."""
        while widget:
            if widget == self:
                return True
            widget = widget.parent()
        return False

    def add_sensor(self, sensor):
        """Add sensor to the logger list if not already present."""
        for index in range(self.sensor_list_widget.count()):
            if self.sensor_list_widget.item(index).text() == sensor:
                return
        self.sensor_list_widget.addItem(sensor)
    
    def remove_sensor(self, sensor):
        """Remove sensor from the logger list."""
        for index in range(self.sensor_list_widget.count()):
            if self.sensor_list_widget.item(index).text() == sensor:
                self.sensor_list_widget.takeItem(index)
                return
    
    def toggle_sensor(self, sensor):
        """Toggle sensor in the logger list."""
        found = False
        for index in range(self.sensor_list_widget.count()):
            if self.sensor_list_widget.item(index).text() == sensor:
                found = True
                break
        if found:
            self.remove_sensor(sensor)
        else:
            self.add_sensor(sensor)
    
    def get_sensors(self):
        """Return a list of sensor names currently selected for logging."""
        sensors = []
        for index in range(self.sensor_list_widget.count()):
            sensors.append(self.sensor_list_widget.item(index).text())
        return sensors


def toggle_logging(logger_widget):
    """
    Toggle CSV logging on/off.
    
    Uses the logger_widget (an instance of CSVLoggerWidget) to get:
      - The log_button for updating text.
      - The list of sensor names via logger_widget.get_sensors().
    """
    global logging_active, logging_start_time, logging_vars, csv_file, csv_writer
    if not logging_active:
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save CSV Log", "", "CSV Files (*.csv)"
        )
        if not fname:
            return  # User cancelled.
        try:
            csv_file = open(fname, 'w', newline='')
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Could not open file:\n{e}")
            return
        csv_writer = csv.writer(csv_file)
        # Retrieve sensor keys from the logger widget's sensor list.
        logging_vars = logger_widget.get_sensors()
        
        # If no variables are selected, log only time.
        if not logging_vars:
            logging_vars = []  # Empty list to indicate only time will be logged
        
        # Write header with time and the selected sensor keys (if any).
        header = ["t"] + logging_vars
        csv_writer.writerow(header)
        csv_file.flush()
        logging_start_time = time.time()
        logging_active = True
        logger_widget.log_button.setText("Stop Logging")
    else:
        logging_active = False
        if csv_file:
            csv_file.close()
        logger_widget.log_button.setText("Start Logging")


def log_data(data_history):
    """
    Called on each update cycle. Writes a new row to the CSV file
    if logging is active.
    """
    global logging_active, logging_start_time, logging_vars, csv_file, csv_writer
    if logging_active and csv_writer:
        t_ms = time.time() - logging_start_time
        row = [t_ms]
        
        if logging_vars:
            for sensor in logging_vars:
                # Write the latest value for each sensor (or an empty string if no data).
                row.append(data_history[sensor][-1] if data_history[sensor] else "")
        csv_writer.writerow(row)
        csv_file.flush()
