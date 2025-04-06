import time
import serial
import threading
from PyQt6 import QtWidgets
from serial.tools import list_ports
from config import BAUD_RATE, MAX_POINTS
from uart import SerialReader  # SerialReader will be updated to accept a comm parameter

class CommProtocol:
    def change_connection(self):
        raise NotImplementedError
    
    def is_connected(self):
        raise NotImplementedError

    def send_sensor(self, sensor, value):
        raise NotImplementedError

    def start_reader(self):
        raise NotImplementedError

class SerialComm(CommProtocol):
    def __init__(self):
        self.ser = None
        self.last_ok_time = time.time()
        self.reader_thread = None

    def select_serial_port(self):
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

    def open_serial_port(self, port):
        try:
            new_ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
            print(f"Serial port {port} opened.")
            return new_ser
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                                           f"Error opening serial port {port}:\n{e}")
            return None

    def change_connection(self):
        # Disconnect if already connected.
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                                               f"Error disconnecting serial port:\n{e}")
            self.ser = None
            return
        port = self.select_serial_port()
        if port:
            new_ser = self.open_serial_port(port)
            if new_ser:
                self.ser = new_ser
                self.last_ok_time = time.time()

    def is_connected(self):
        return self.ser is not None and self.ser.is_open

    def send_sensor(self, sensor, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be a number.")
        if self.ser and self.ser.is_open:
            message = f"{sensor}:{value:.2f}\r\n"
            try:
                self.ser.write(message.encode("utf-8"))
                self.ser.flush()
            except (serial.SerialException, OSError) as e:
                print(f"Error sending data on serial port: {e}")
                QtWidgets.QMessageBox.critical(None, "Serial Port Error", f"Error sending data:\n{e}")
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
        else:
            QtWidgets.QMessageBox.warning(None, "Serial Port Warning", "Serial port is not open.")

    def start_reader(self):
        if self.reader_thread is None or not self.reader_thread.is_alive():
            reader = SerialReader(self)  # pass self to let the reader update comm attributes
            thread = threading.Thread(target=reader.read_serial, daemon=True)
            thread.start()
            self.reader_thread = thread
