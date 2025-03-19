import csv
import time
from PyQt6 import QtWidgets

# Global logging variables (shared with data.py if needed)
logging_active = False
logging_start_time = None
logging_vars = []  # List of sensor keys to log
csv_file = None
csv_writer = None

def toggle_logging(log_button, log_checkboxes, sensor_keys):
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
        logging_vars = [sensor for sensor, cb in log_checkboxes.items() if cb.isChecked()]
        header = ["t"] + logging_vars
        csv_writer.writerow(header)
        csv_file.flush()
        logging_start_time = time.time()
        logging_active = True
        log_button.setText("Stop Logging")
    else:
        logging_active = False
        if csv_file:
            csv_file.close()
        log_button.setText("Start Logging")

def log_data(data_history):
    global logging_active, logging_start_time, logging_vars, csv_file, csv_writer
    if logging_active and logging_vars and csv_writer:
        t_ms = time.time() - logging_start_time
        row = [t_ms]
        for sensor in logging_vars:
            # Write latest value for sensor (or empty string if no data)
            row.append(data_history[sensor][-1] if data_history[sensor] else "")
        csv_writer.writerow(row)
        csv_file.flush()
