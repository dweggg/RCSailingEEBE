import sys
import serial
from serial.tools import list_ports
from config import BAUD_RATE

# This will hold the serial connection
ser = None

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
    global ser
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
        print(f"Serial port {port} opened.")
    except serial.SerialException as e:
        sys.exit(f"Error opening serial port {port}: {e}")
    return ser

def get_serial_connection():
    return ser

def send_sensor(sensor, value):
    """Send a sensor value over the serial port using the given protocol.
    
    Protocol format: "KEY:%.?f\r\n" where ? depends on the value precision.
    """
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number.")

    if ser and ser.is_open:
        message = f"{sensor}:{value:.2f}\r\n"  # Format with five decimal places
        try:
            ser.write(message.encode("utf-8"))  # Send the message
            ser.flush()
        except serial.SerialException as e:
            print(f"Error sending data: {e}")
    else:
        print("Serial port is not open.")
