import sys
import serial
from serial.tools import list_ports
from config import BAUD_RATE
from PyQt6 import QtWidgets

# This will hold the serial connection
ser = None

def select_serial_port():
    ports = [port.device for port in list_ports.comports()]
    if not ports:
        QtWidgets.QMessageBox.critical(None, "Serial Port Error", "No serial ports found.")
        return None
    port, ok = QtWidgets.QInputDialog.getItem(
        None, "Select Serial Port", "Serial Port:", ports, 0, False
    )
    if not ok:
        QtWidgets.QMessageBox.warning(None, "Serial Port Selection", "No serial port selected.")
        return None
    return port

def open_serial_port(port):
    global ser
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
        print(f"Serial port {port} opened.")
    except serial.SerialException as e:
        QtWidgets.QMessageBox.critical(None, "Serial Port Error", f"Error opening serial port {port}:\n{e}")
        ser = None
    return ser

def get_serial_connection():
    return ser

def send_sensor(sensor, value):
    """Send a sensor value over the serial port using the given protocol.
    
    Protocol format: "KEY:%.?f\r\n" where ? depends on the value precision.
    """
    global ser
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number.")
    if ser and ser.is_open:
        message = f"{sensor}:{value:.2f}\r\n"
        try:
            ser.write(message.encode("utf-8"))
            ser.flush()
        except (serial.SerialException, OSError) as e:
            # Log the error and close the port to avoid repeated errors.
            print(f"Error sending data on serial port: {e}")
            QtWidgets.QMessageBox.critical(None, "Serial Port Error", f"Error sending data:\n{e}")
            try:
                ser.close()
            except Exception:
                pass
            ser = None
    else:
        QtWidgets.QMessageBox.warning(None, "Serial Port Warning", "Serial port is not open.")

