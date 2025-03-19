import sys
import serial
from serial.tools import list_ports
from config import BAUD_RATE

def select_serial_port():
    ports = [port.device for port in list_ports.comports()]
    if not ports:
        sys.exit("No serial ports found.")
    from PyQt6 import QtWidgets
    port, ok = QtWidgets.QInputDialog.getItem(
        None, "Select Serial Port", "Serial Port:", ports, 0, False
    )
    if not ok:
        sys.exit("No serial port selected.")
    return port

def open_serial_port(port):
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
    except serial.SerialException as e:
        sys.exit(f"Error opening serial port {port}: {e}")
    return ser
