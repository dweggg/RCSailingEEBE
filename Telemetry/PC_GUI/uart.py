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

def send_signal(comm, signal, value):
    """Send a signal value over the serial port using the given protocol.
    
    Protocol format: "KEY:%.?f\r\n"
    """
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number.")
    if comm.ser and comm.ser.is_open:
        message = f"{signal}:{value:.2f}\r\n"
        try:
            comm.ser.write(message.encode("utf-8"))
            comm.ser.flush()
        except (serial.SerialException, OSError) as e:
            print(f"Error sending data on serial port: {e}")
            QtWidgets.QMessageBox.critical(None, "Serial Port Error", f"Error sending data:\n{e}")
            try:
                comm.ser.close()
            except Exception:
                pass
            comm.ser = None
    else:
        QtWidgets.QMessageBox.warning(None, "Serial Port Warning", "Serial port is not open.")

last_ok_time = 0

def change_serial_port():
    global ser, last_ok_time
    # Disconnect if already connected.
    if ser is not None:
        try:
            ser.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                f"Error disconnecting serial port:\n{e}")
        ser = None
        return
    port = select_serial_port()
    if port:
        new_ser = open_serial_port(port)
        if new_ser:
            ser = new_ser
            import time
            last_ok_time = time.time()

class SerialReader:
    def __init__(self, comm):
        self._running = True
        self.comm = comm

    def read_serial(self):
        import time
        from data import data_history, start_time
        from config import MAX_POINTS  # assuming MAX_POINTS is in config
        import re
        pattern = re.compile(r"^-?\d+\.\d\d$")
        while self._running:
            if self.comm.ser is not None:
                try:
                    if self.comm.ser.in_waiting:
                        raw_bytes = self.comm.ser.read(self.comm.ser.in_waiting)
                        raw_lines = raw_bytes.decode('utf-8', errors='ignore').splitlines()
                        for line in raw_lines:
                            line = line.strip()
                            if line == "OK":
                                self.comm.last_ok_time = time.time()
                            if not line or ':' not in line:
                                continue
                            key, value_str = line.split(':', 1)
                            # Only use complete frames with a proper float format (two decimals)
                            if not pattern.match(value_str):
                                continue
                            try:
                                value = float(value_str)
                            except ValueError:
                                continue
                            if key in data_history:
                                data_history[key].append((value, time.time() - start_time))
                                if len(data_history[key]) > MAX_POINTS:
                                    data_history[key] = data_history[key][-MAX_POINTS:]
                except (OSError, serial.SerialException) as e:
                    print(f"Error reading from serial port: {e}")
                    QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                        f"Error reading from serial port:\n{e}\n\nThe port will be closed.")
                    try:
                        self.comm.ser.close()
                    except Exception:
                        pass
                    self.comm.ser = None
            time.sleep(0.005)

    def stop(self):
        self._running = False

def start_serial_reader(comm):
    import threading
    reader = SerialReader(comm)
    thread = threading.Thread(target=reader.read_serial, daemon=True)
    thread.start()
    return thread

