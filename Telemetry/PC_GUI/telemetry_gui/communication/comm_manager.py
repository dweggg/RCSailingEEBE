"""
Communication Manager Module
===========================

Provides a unified interface for various communication protocols
(serial, CAN, etc.) with improved error handling and abstraction.
"""

import time
import threading
import re
from typing import Optional, Dict, Any, Callable
import serial
from serial.tools import list_ports
from PyQt6 import QtWidgets

class CommunicationProtocol:
    """Base class for communication protocols."""
    
    def __init__(self):
        self.is_open = False
        self.last_ok_time = 0
        self.on_data_received = None
    
    def connect(self) -> bool:
        """
        Establish connection with the device.
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    def is_connected(self) -> bool:
        """
        Check if currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.is_open
    
    def send_message(self, key: str, value: float) -> bool:
        """
        Send a message with the given key and value.
        
        Args:
            key: Message identifier
            value: Value to send
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_message()")
    
    def set_data_callback(self, callback: Callable[[str, float, float], None]) -> None:
        """
        Set callback for received data.
        
        Args:
            callback: Function to call with (signal_key, value, timestamp)
        """
        self.on_data_received = callback
    
    def start(self) -> None:
        """Start communication (reader threads, etc.)."""
        raise NotImplementedError("Subclasses must implement start()")
    
    def stop(self) -> None:
        """Stop communication (reader threads, etc.)."""
        raise NotImplementedError("Subclasses must implement stop()")


class SerialProtocol(CommunicationProtocol):
    """Serial communication protocol implementation."""
    
    def __init__(self, baud_rate: int = 115200, timeout: float = 0.1):
        """
        Initialize the serial protocol.
        
        Args:
            baud_rate: Baud rate for serial communication
            timeout: Read timeout in seconds
        """
        super().__init__()
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.port = None
        self.ser: Optional[serial.Serial] = None
        self.reader_thread = None
        self._running = False
    
    def select_port(self) -> Optional[str]:
        """
        Show a dialog to select a serial port.
        
        Returns:
            Selected port name or None if cancelled
        """
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
    
    def connect(self) -> bool:
        """
        Connect to a serial port selected by the user.
        
        Returns:
            True if successful, False otherwise
        """
        self.port = self.select_port()
        if not self.port:
            return False
            
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            self.is_open = True
            self.last_ok_time = time.time()
            print(f"Serial port {self.port} opened successfully.")
            return True
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(None, "Serial Port Error", 
                                          f"Error opening port {self.port}:\n{e}")
            self.ser = None
            self.is_open = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the serial port.
        
        Returns:
            True if successful, False otherwise
        """
        if self.ser:
            try:
                self.ser.close()
                self.is_open = False
                self.ser = None
                print(f"Serial port {self.port} closed.")
                return True
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                                              f"Error closing port {self.port}:\n{e}")
                return False
        return True
    
    def toggle_connection(self) -> bool:
        """
        Toggle connection state (connect if disconnected, disconnect if connected).
        
        Returns:
            New connection state (True if connected, False if disconnected)
        """
        if self.is_connected():
            self.stop()
            self.disconnect()
            return False
        else:
            success = self.connect()
            if success:
                self.start()
            return success
    
    def send_message(self, key: str, value: float) -> bool:
        """
        Send a message over the serial port.
        
        Args:
            key: Signal key
            value: Value to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            QtWidgets.QMessageBox.warning(None, "Serial Port Warning", 
                                         "Serial port is not open.")
            return False
            
        try:
            # Format: "KEY:%.2f\r\n"
            message = f"{key}:{value:.2f}\r\n"
            self.ser.write(message.encode("utf-8"))
            self.ser.flush()
            return True
        except (serial.SerialException, OSError) as e:
            print(f"Error sending data on serial port: {e}")
            QtWidgets.QMessageBox.critical(None, "Serial Port Error", 
                                          f"Error sending data:\n{e}")
            self.disconnect()
            return False
    
    def start(self) -> None:
        """Start the reader thread for receiving serial data."""
        if not self.is_connected():
            return
            
        self._running = True
        self.reader_thread = threading.Thread(target=self._read_serial, daemon=True)
        self.reader_thread.start()
    
    def stop(self) -> None:
        """Stop the reader thread."""
        self._running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
    
    def _read_serial(self) -> None:
        """Reader thread function that processes incoming serial data."""
        # Regex to validate data format (e.g., "123.45" - floating point with 2 decimals)
        pattern = re.compile(r"^-?\d+\.\d\d$")
        
        while self._running and self.ser:
            try:
                if self.ser.in_waiting:
                    raw_bytes = self.ser.read(self.ser.in_waiting)
                    raw_lines = raw_bytes.decode('utf-8', errors='ignore').splitlines()
                    
                    for line in raw_lines:
                        line = line.strip()
                        
                        # Handle OK heartbeat messages
                        if line == "OK":
                            self.last_ok_time = time.time()
                            continue
                            
                        # Skip invalid lines
                        if not line or ':' not in line:
                            continue
                            
                        # Parse key:value format
                        key, value_str = line.split(':', 1)
                        
                        # Validate value format
                        if not pattern.match(value_str):
                            continue
                            
                        try:
                            value = float(value_str)
                            timestamp = time.time()
                            
                            # Call the data callback if set
                            if self.on_data_received:
                                self.on_data_received(key, value, timestamp)
                        except ValueError:
                            continue
                        
            except (OSError, serial.SerialException) as e:
                print(f"Error reading from serial port: {e}")
                QtWidgets.QMessageBox.critical(None, "Serial Port Error",
                    f"Error reading from serial port:\n{e}\n\nThe port will be closed.")
                
                try:
                    self.disconnect()
                except Exception:
                    pass
                    
                break
                
            # Short sleep to avoid excessive CPU usage
            time.sleep(0.005)


class CommunicationManager:
    """
    Manages communication protocols and provides a unified interface.
    """
    
    def __init__(self, protocol: CommunicationProtocol = None):
        """
        Initialize the communication manager.
        
        Args:
            protocol: Initial communication protocol to use
        """
        self.protocol = protocol or SerialProtocol()
        self.data_callbacks = []
    
    def toggle_connection(self) -> bool:
        """
        Toggle the connection state.
        
        Returns:
            New connection state
        """
        if isinstance(self.protocol, SerialProtocol):
            return self.protocol.toggle_connection()
        elif self.is_connected():
            self.disconnect()
            return False
        else:
            return self.connect()
    
    def connect(self) -> bool:
        """
        Establish connection with the device.
        
        Returns:
            True if successful, False otherwise
        """
        success = self.protocol.connect()
        if success:
            self.protocol.start()
        return success
    
    def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            True if successful, False otherwise
        """
        if self.protocol.is_connected():
            self.protocol.stop()
            return self.protocol.disconnect()
        return True
    
    def is_connected(self) -> bool:
        """
        Check if currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.protocol.is_connected()
    
    def send_message(self, key: str, value: float) -> bool:
        """
        Send a message with the given key and value.
        
        Args:
            key: Message identifier
            value: Value to send
            
        Returns:
            True if successful, False otherwise
        """
        return self.protocol.send_message(key, value)
    
    def register_data_callback(self, callback: Callable[[str, float, float], None]) -> None:
        """
        Register a callback for data reception.
        
        Args:
            callback: Function to call with (signal_key, value, timestamp)
        """
        if callback not in self.data_callbacks:
            self.data_callbacks.append(callback)
        
        # Set the protocol callback to our dispatcher
        if not self.protocol.on_data_received:
            self.protocol.set_data_callback(self._dispatch_data)
    
    def unregister_data_callback(self, callback: Callable[[str, float, float], None]) -> None:
        """
        Unregister a previously registered callback.
        
        Args:
            callback: Previously registered callback function
        """
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def _dispatch_data(self, key: str, value: float, timestamp: float) -> None:
        """
        Dispatch received data to all registered callbacks.
        
        Args:
            key: Signal key
            value: Signal value
            timestamp: Time when the data was received
        """
        for callback in self.data_callbacks:
            try:
                callback(key, value, timestamp)
            except Exception as e:
                print(f"Error in data callback: {e}")
    
    @property
    def last_ok_time(self) -> float:
        """
        Get the timestamp of the last received OK message.
        
        Returns:
            Timestamp of last OK message
        """
        return self.protocol.last_ok_time