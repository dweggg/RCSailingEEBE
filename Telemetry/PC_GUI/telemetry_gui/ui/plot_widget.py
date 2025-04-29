"""
Plot Widget Module
================

Provides interactive plot widgets for data visualization.
"""

import random
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Set, Any
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui

from telemetry_gui.ui.focus_manager import FocusManager
from telemetry_gui.data.data_manager import DataManager
from telemetry_gui.communication.comm_manager import CommunicationManager


class DynamicPlot(QtWidgets.QGroupBox):
    """Interactive plot widget that can display multiple signals."""
    
    # Signal emitted when this plot is selected
    selected_signal = QtCore.pyqtSignal(object)
    
    # Class variable to store predefined colors for signals
    COLORS = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 255, 0),    # Yellow
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 128, 0),    # Orange
        (128, 0, 255),    # Purple
        (0, 128, 255),    # Light blue
    ]
    
    def __init__(self, title="Plot", parent=None, tiling_area=None, data_manager=None, comm_manager=None):
        """
        Initialize the plot widget.
        
        Args:
            title: Title for the plot widget
            parent: Parent widget
            tiling_area: Reference to parent tiling area
            data_manager: Data manager for accessing signal data
            comm_manager: Communication manager for sending signals
        """
        super().__init__(title, parent)
        self.setMinimumSize(200, 200)
        self.selected = False
        self.tiling_area = tiling_area
        self.data_manager = data_manager
        self.comm_manager = comm_manager
        
        # Allow the widget to gain focus when clicked but don't show focus rect
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)

        # Signal tracking
        self.signal_keys_assigned: Set[str] = set()
        self.signal_curves: Dict[str, pg.PlotDataItem] = {}
        self.signal_colors: Dict[str, Tuple[int, int, int]] = {}
        
        # Display mode variables
        self.display_text_size = 24
        self.tx_widgets = {}
        self.rx_widgets = {}
        self.last_tx_values = {}
        
        # Mode tracking: "plot", "display", or "xy"
        self.mode = "plot"
        
        # Cursor variables
        self.cursors_active = False
        self.cursor1 = None
        self.cursor2 = None
        self.cursor_info_label = None
        self.cursor_link_combo = None
        self.cursor_linked_signal = None
        self.cursor1_rel_pos = 1/3
        self.cursor2_rel_pos = 2/3
        
        # XY Plot variables
        self.xy_curve = None
        self.xy_marker = None
        
        # Initialize UI components
        self._init_ui()
        
        # Accept drops for drag and drop functionality
        self.setAcceptDrops(True)
        
    def _init_ui(self):
        """Initialize plot UI components."""
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 25, 10, 10)  # left, top, right, bottom
        
        # Create pyqtgraph plot widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
        # Add grid
        self.plot_widget.showGrid(x=True, y=True)
        
        # Add legend (positioning in bottom-right corner)
        self.legend = self.plot_widget.addLegend(offset=(-10, 10))
        self.legend.anchor = (0, 0)
        
        # Set the border color
        self.setStyleSheet("QGroupBox { border: 2px solid gray; }")
        
        # Add context menu for right-click functionality
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Create a QLineEdit to input time window (in seconds) inside the plot
        self.time_window_edit = QtWidgets.QLineEdit(self.plot_widget)
        self.time_window_edit.setPlaceholderText("Time Window (s)")
        self.time_window_edit.setFixedWidth(100)
        self.time_window_edit.setStyleSheet(
            "background-color: rgba(200, 200, 200, 150); border: 1px solid gray; border-radius: 5px;"
        )
        self.time_window_edit.editingFinished.connect(self.update_plot)
        
        # Remove button
        self.remove_button = QtWidgets.QPushButton("X")
        self.remove_button.setParent(self)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.move(self.width() - 25, 5)
        self.remove_button.setStyleSheet(
            "background-color: rgba(255, 0, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.remove_button.clicked.connect(self.remove_self)
        
        # Toggle mode button
        self.toggle_button = QtWidgets.QPushButton("P")
        self.toggle_button.setFixedSize(40, 20)
        self.toggle_button.setStyleSheet(
            "background-color: rgba(0, 255, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.toggle_button.setParent(self)
        self.toggle_button.move(self.width() - 70, 5)
        
        # Cursor toggle button
        self.cursor_button = QtWidgets.QPushButton("C")
        self.cursor_button.setFixedSize(40, 20)
        self.cursor_button.setStyleSheet(
            "background-color: rgba(0, 120, 215, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.cursor_button.clicked.connect(self.toggle_cursors)
        self.cursor_button.setParent(self)
        self.cursor_button.move(self.width() - 115, 5)
        
        # Create display container with a top control for text size
        self.display_container = QtWidgets.QWidget(self)
        self.display_container_layout = QtWidgets.QVBoxLayout(self.display_container)
        self.display_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a QLineEdit for text size
        self.text_size_edit = QtWidgets.QLineEdit(self.display_container)
        self.text_size_edit.setPlaceholderText("Text Size")
        self.text_size_edit.setFixedWidth(50)
        self.text_size_edit.setStyleSheet(
            "background-color: rgba(200, 200, 200, 150); border: 1px solid gray; border-radius: 5px;"
        )
        self.text_size_edit.setText(str(self.display_text_size))
        self.text_size_edit.editingFinished.connect(self.process_text_size_edit)
        
        # Sub-layout for signal display widgets
        self.widget_display_layout = QtWidgets.QVBoxLayout()
        self.display_container_layout.addLayout(self.widget_display_layout)
        
        self.display_container.hide()
        layout.addWidget(self.display_container)
        
        # Initialize cursor functionality (hidden by default)
        self._init_cursor_elements()
        
        # Initialize timestamp tracking for legend updates
        self.last_legend_update = 0
        
    def _init_cursor_elements(self):
        """Initialize cursor elements (hidden initially)."""
        pen_cursor = pg.mkPen('c', width=1, style=QtCore.Qt.PenStyle.DashLine)
        self.cursor1_v = pg.InfiniteLine(angle=90, movable=True, pen=pen_cursor)
        self.cursor1_h = pg.InfiniteLine(angle=0, movable=True, pen=pen_cursor)
        self.cursor2_v = pg.InfiniteLine(angle=90, movable=True, pen=pen_cursor)
        self.cursor2_h = pg.InfiniteLine(angle=0, movable=True, pen=pen_cursor)
        
        self.cursor1_v.hide(); self.cursor1_h.hide()
        self.cursor2_v.hide(); self.cursor2_h.hide()
        
        self.plot_widget.addItem(self.cursor1_v)
        self.plot_widget.addItem(self.cursor1_h)
        self.plot_widget.addItem(self.cursor2_v)
        self.plot_widget.addItem(self.cursor2_h)
        
        self.cursor_info = pg.TextItem("", anchor=(0, 0))
        self.cursor_info.hide()
        self.plot_widget.addItem(self.cursor_info)
        
        self.cursor1_v.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor1_h.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor2_v.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor2_h.sigPositionChanged.connect(self.update_cursor_info)
        
    def remove_self(self):
        """Safely remove itself from TilingArea."""
        # Remove cursors if active
        if self.cursors_active and self.cursor1 is not None:
            self.remove_cursors()
            
        # Call the tiling area to remove this plot
        if self.tiling_area:
            self.tiling_area.remove_plot(self)
            
    def resizeEvent(self, event):
        """Update button positions when resizing the plot."""
        super().resizeEvent(event)
        self.remove_button.move(self.width() - 25, 5)
        self.toggle_button.move(self.width() - 70, 5)
        self.cursor_button.move(self.width() - 115, 5)
        
        # Position time_window_edit and text_size_edit to bottom-right corners
        margin = 10
        self.time_window_edit.move(
            self.plot_widget.width() - self.time_window_edit.width() - margin,
            self.plot_widget.height() - self.time_window_edit.height() - margin
        )
        
        if self.display_container.isVisible():
            self.text_size_edit.move(
                self.display_container.width() - self.text_size_edit.width() - margin,
                self.display_container.height() - self.text_size_edit.height() - margin
            )
            self.text_size_edit.raise_()
            
        # Update cursor info label position if it exists
        if self.cursor_info_label and self.cursor_info_label.isVisible():
            self.cursor_info_label.move(10, 35)
        
        # Update cursor link combo position if it exists
        if self.cursor_link_combo and self.cursor_link_combo.isVisible():
            self.cursor_link_combo.move(10, 120)
            
        # Update cursor positions to maintain their relative positions in the view
        if self.cursors_active and self.cursor1 is not None and self.cursor1.isVisible():
            self.update_cursor_positions()
        
    def mousePressEvent(self, event):
        """Handle mouse press events to set focus."""
        FocusManager.set_active(self)
        self.selected_signal.emit(self)
        super().mousePressEvent(event)
        
        # Update cursor information if cursors are active
        if self.cursors_active and self.cursor1 is not None and self.cursor1.isVisible():
            self.update_cursor_info()
        
    def focusInEvent(self, event):
        """Override focus in event to update visual appearance."""
        # Change border color to indicate focus without changing size
        self.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        """Override focus out event to update visual appearance."""
        # Restore normal border color
        self.setStyleSheet("QGroupBox { border: 2px solid gray; }")
        super().focusOutEvent(event)
        
    def update_plot(self):
        """Updates the plot based on the current mode."""
        if not self.data_manager:
            return
            
        if self.mode == "xy":
            self.update_xy_plot()
            return
        elif self.mode == "display":
            self.update_display_widgets()
            return
            
        # For regular time-series mode
        self.update_legend()
        current_time = self.data_manager.current_time()
        data_history = self.data_manager.data_history
        
        for signal_key in self.signal_keys_assigned:
            if signal_key not in data_history:
                continue
                
            signal_data = data_history[signal_key]
            if not signal_data:
                continue
                
            # Get times and values for plotting
            values = [point[0] for point in signal_data]
            timestamps = [point[1] for point in signal_data]
            
            # Update the plot
            if signal_key in self.signal_curves:
                self.signal_curves[signal_key].setData(timestamps, values)
                
        # Apply time window if specified
        try:
            time_window = float(self.time_window_edit.text())
        except ValueError:
            time_window = 0
            
        if time_window > 0:
            self.plot_widget.setXRange(max(0, current_time - time_window), current_time)
        else:
            self.plot_widget.enableAutoRange(axis='x')
            
    def update_xy_plot(self):
        """Updates the XY plot using the first signal as x-axis and the second as y-axis."""
        if not self.data_manager or len(self.signal_keys_assigned) < 2:
            return
            
        signal_keys = list(self.signal_keys_assigned)
        x_signal = signal_keys[0]
        y_signal = signal_keys[1]
        current_time = self.data_manager.current_time()
        data_history = self.data_manager.data_history
        
        try:
            time_window = float(self.time_window_edit.text())
        except ValueError:
            time_window = 0
            
        x_data = data_history.get(x_signal, [])
        y_data = data_history.get(y_signal, [])
        
        if time_window > 0:
            x_data = [entry for entry in x_data if entry[1] >= current_time - time_window]
            y_data = [entry for entry in y_data if entry[1] >= current_time - time_window]
            
        n = min(len(x_data), len(y_data))
        if n == 0:
            return
            
        x_vals = [x_data[i][0] for i in range(n)]
        y_vals = [y_data[i][0] for i in range(n)]
        
        if hasattr(self, "xy_curve") and self.xy_curve is not None:
            self.xy_curve.setData(x_vals, y_vals)
        else:
            self.xy_curve = self.plot_widget.plot(x_vals, y_vals, pen=pg.mkPen(width=2), name="")
            
        if not hasattr(self, "xy_marker") or self.xy_marker is None:
            self.xy_marker = pg.ScatterPlotItem(
                size=10,
                pen=pg.mkPen(None),
                brush=pg.mkBrush('r')
            )
            self.plot_widget.addItem(self.xy_marker)
            
        self.xy_marker.setData([x_vals[-1]], [y_vals[-1]])
        
        try:
            from telemetry_gui.data.signals import get_signal_name
            x_name = get_signal_name(x_signal)
            y_name = get_signal_name(y_signal)
        except ImportError:
            x_name = x_signal
            y_name = y_signal
            
        self.plot_widget.setLabel('bottom', x_name)
        self.plot_widget.setLabel('left', y_name)
            
    def update_display_widgets(self):
        """Update display widget text for each signal."""
        if not self.data_manager:
            return
            
        data_history = self.data_manager.data_history
        for signal in self.signal_keys_assigned:
            value = None
            if signal in data_history and data_history[signal]:
                value = data_history[signal][-1][0]
            
            try:
                from telemetry_gui.data.signals import get_signal_direction
                direction = get_signal_direction(signal)
            except ImportError:
                # Default direction if can't import
                direction = 'RX'
                
            if direction == 'TX':
                current_value = self.last_tx_values.get(signal, value)
                container, name_label, input_field = self.tx_widgets[signal]
                if not input_field.hasFocus():
                    input_field.setText(str(current_value) if current_value is not None else "")
            else:  # RX
                container, name_label, output_field = self.rx_widgets[signal]
                output_field.setText(str(value) if value is not None else "No data available")
                
    def update_legend(self):
        """Updates the legend based on current signal streams (rate-limited)."""
        if not self.data_manager:
            return
            
        current_time = self.data_manager.current_time()
        
        # Only update legend once per second
        if current_time - self.last_legend_update < 1.0:
            return
            
        self.last_legend_update = current_time
            
        # Clear existing legend
        if hasattr(self, "legend"):
            self.legend.clear()
            
        # In 'plot' mode, show the signal name with the 1s datarate
        if self.mode == "plot":
            data_history = self.data_manager.data_history
            for signal in self.signal_keys_assigned:
                if signal in self.signal_curves:
                    signal_data = data_history.get(signal, [])
                    count = 0
                    
                    # Count data points in the last second
                    for _, t in reversed(signal_data):
                        if t >= current_time - 1:
                            count += 1
                        else:
                            break
                    
                    try:
                        from telemetry_gui.data.signals import get_signal_name
                        signal_name = get_signal_name(signal)
                    except ImportError:
                        signal_name = signal
                        
                    label = f"{signal_name} ({count} Hz)"
                    self.legend.addItem(self.signal_curves[signal], label)
        else:
            # In other modes, simply display the signal name
            for signal in self.signal_keys_assigned:
                if signal in self.signal_curves:
                    try:
                        from telemetry_gui.data.signals import get_signal_name
                        signal_name = get_signal_name(signal)
                    except ImportError:
                        signal_name = signal
                        
                    self.legend.addItem(self.signal_curves[signal], signal_name)
    
    def add_signal(self, signal_key: str) -> bool:
        """
        Add a signal to the plot.
        
        Args:
            signal_key: Signal identifier to add
            
        Returns:
            True if added successfully, False otherwise
        """
        if self.mode == "xy" and len(self.signal_keys_assigned) >= 2:
            # XY mode only supports 2 signals (x and y)
            return False
            
        # Check if signal already in plot
        if signal_key in self.signal_keys_assigned:
            return False
            
        # Add to tracking collections
        self.signal_keys_assigned.add(signal_key)
        
        # In plot or xy mode, add the curve
        if self.mode != "display":
            color = self.get_color(signal_key)
            pen = pg.mkPen(color=color, width=2)
            
            try:
                from telemetry_gui.data.signals import get_signal_name
                signal_name = get_signal_name(signal_key)
            except ImportError:
                signal_name = signal_key
                
            curve = self.plot_widget.plot([], [], name=signal_name, pen=pen)
            self.signal_curves[signal_key] = curve
            
        # If in display mode, add the corresponding display widget
        if self.mode == "display":
            self.add_display_widget(signal_key)
            
        return True
    
    def add_display_widget(self, signal_key):
        """
        Add a display widget for a signal based on its direction.
        
        Args:
            signal_key: Signal identifier
        """
        try:
            from telemetry_gui.data.signals import get_signal_name, get_signal_direction
            signal_name = get_signal_name(signal_key)
            direction = get_signal_direction(signal_key)
        except ImportError:
            signal_name = signal_key
            direction = 'RX'  # Default to receive if can't determine
            
        if direction == 'TX':
            if signal_key not in self.tx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(signal_name + ": ")
                name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                editable_input = QtWidgets.QLineEdit()
                editable_input.setPlaceholderText(f"Enter {signal_key} value...")
                editable_input.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                editable_input.returnPressed.connect(
                    lambda signal=signal_key, input_field=editable_input: 
                    self.on_return_pressed(signal, input_field)
                )
                h_layout.addWidget(editable_input)
                
                self.tx_widgets[signal_key] = (container, name_label, editable_input)
                self.widget_display_layout.addWidget(container)
        else:
            if signal_key not in self.rx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(signal_name + ": ")
                name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                output_field = QtWidgets.QLineEdit()
                output_field.setReadOnly(True)
                output_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(output_field)
                
                self.rx_widgets[signal_key] = (container, name_label, output_field)
                self.widget_display_layout.addWidget(container)
    
    def on_return_pressed(self, signal_key, input_field):
        """
        Handle Enter key press for TX signal inputs: send the value and update display.
        
        Args:
            signal_key: Signal identifier
            input_field: Input field widget
        """
        try:
            new_value = float(input_field.text())
        except ValueError:
            return
            
        # Send the signal if comm_manager is available
        if self.comm_manager:
            self.comm_manager.send_message(signal_key, new_value)
            
        # Update data history if data_manager is available
        if self.data_manager:
            self.data_manager.add_data_point(signal_key, new_value)
            
        # Store the value for display
        self.last_tx_values[signal_key] = new_value
        
        # Visual feedback
        input_field.setStyleSheet(f"background-color: green; font-size: {self.display_text_size}px; font-weight: bold;")
        QtCore.QTimer.singleShot(150, lambda: 
            input_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
        )
        
        print(f"Updated {signal_key} with value: {new_value}")
    
    def remove_signal(self, signal_key: str) -> bool:
        """
        Remove a signal from the plot.
        
        Args:
            signal_key: Signal identifier to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if signal_key not in self.signal_keys_assigned:
            return False
            
        # Remove from tracking collections
        self.signal_keys_assigned.remove(signal_key)
        
        # Remove the curve from the plot
        if signal_key in self.signal_curves:
            self.plot_widget.removeItem(self.signal_curves[signal_key])
            del self.signal_curves[signal_key]
            
        # Remove display widgets
        if signal_key in self.tx_widgets:
            widget = self.tx_widgets.pop(signal_key)[0]
            widget.deleteLater()
        if signal_key in self.rx_widgets:
            widget = self.rx_widgets.pop(signal_key)[0]
            widget.deleteLater()
            
        # Remove from legend (need to recreate legend)
        self._rebuild_legend()
        
        return True
        
    def _rebuild_legend(self):
        """Rebuild the plot legend after changes to the curves."""
        # Remove existing legend
        if hasattr(self, 'legend') and self.legend:
            self.plot_widget.removeItem(self.legend)
            
        # Create a new legend
        self.legend = self.plot_widget.addLegend(offset=(-10, 10))
        self.legend.anchor = (0, 0)
        
    def toggle_mode(self):
        """Cycle through three modes: plot, display, and xy."""
        if self.mode == "plot":
            # Hide cursor button and cursor elements when switching to other modes
            self.cursor_button.hide()
            if self.cursors_active:
                self.hide_cursors()
                
            self.mode = "display"
            self.toggle_button.setText("D")
            self.plot_widget.hide()
            self.display_container.show()
            self.remove_button.raise_()
            self.toggle_button.raise_()
            self.text_size_edit.raise_()
            self.populate_display_mode()
        elif self.mode == "display":
            # Save the signal keys before switching to XY mode
            self._backup_signal_keys = list(self.signal_keys_assigned)
            self.mode = "xy"
            self.toggle_button.setText("XY")
            self.display_container.hide()
            self.plot_widget.show()
            
            # Clear the plot for xy mode
            self.plot_widget.clear()
            
            # In xy mode we limit to 2 signals
            if len(self._backup_signal_keys) >= 2:
                self.signal_keys_assigned = set(self._backup_signal_keys[:2])
            
            # Create XY curve if needed
            if not hasattr(self, "xy_curve") or self.xy_curve is None:
                self.xy_curve = self.plot_widget.plot(pen=pg.mkPen(width=2), name="")
            self.update_xy_plot()
        elif self.mode == "xy":
            self.mode = "plot"
            self.toggle_button.setText("P")
            self.display_container.hide()
            self.plot_widget.show()
            
            # Show cursor button in plot mode
            self.cursor_button.show()
            
            # Clean up XY mode components
            if hasattr(self, "xy_curve") and self.xy_curve is not None:
                self.plot_widget.removeItem(self.xy_curve)
                self.xy_curve = None
            if hasattr(self, "xy_marker") and self.xy_marker is not None:
                self.plot_widget.removeItem(self.xy_marker)
                self.xy_marker = None
                
            # Restore backed up signals
            if hasattr(self, "_backup_signal_keys"):
                self.signal_keys_assigned = set(self._backup_signal_keys)
                del self._backup_signal_keys
                
            # Clear the plot and reinitialize
            self.plot_widget.clear()
            
            # Recreate legend
            self.legend = self.plot_widget.addLegend(offset=(-10, 10))
            self.legend.anchor = (0, 0)
            
            # Recreate curves for each signal
            self.signal_curves = {}
            for signal_key in self.signal_keys_assigned:
                color = self.get_color(signal_key)
                
                try:
                    from telemetry_gui.data.signals import get_signal_name
                    signal_name = get_signal_name(signal_key)
                except ImportError:
                    signal_name = signal_key
                    
                self.signal_curves[signal_key] = self.plot_widget.plot(
                    [], [], 
                    name=signal_name, 
                    pen=pg.mkPen(color=color, width=2)
                )
                
            # Reset labels
            self.plot_widget.setLabel('bottom', "")
            self.plot_widget.setLabel('left', "")
            
            # Update plot
            self.update_plot()
            
            # Restore cursors if they were active before
            if self.cursors_active:
                self.show_cursors()
    
    def populate_display_mode(self):
        """(Re)populate the display layout with widgets for each signal."""
        # Clear previous widgets
        while self.widget_display_layout.count():
            item = self.widget_display_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                
        # Add widgets for each signal
        for signal_key in self.signal_keys_assigned:
            try:
                from telemetry_gui.data.signals import get_signal_direction
                direction = get_signal_direction(signal_key)
            except ImportError:
                direction = 'RX'  # Default to receive if can't determine
                
            if direction == 'TX':
                if signal_key not in self.tx_widgets:
                    self.add_display_widget(signal_key)
                else:
                    self.widget_display_layout.addWidget(self.tx_widgets[signal_key][0])
            else:
                if signal_key not in self.rx_widgets:
                    self.add_display_widget(signal_key)
                else:
                    self.widget_display_layout.addWidget(self.rx_widgets[signal_key][0])
                    
        # Update the display widgets with current values
        self.update_display_widgets()
    
    def get_color(self, signal_key):
        """
        Return a color for the signal. If not assigned, generate and store a new color.
        
        Args:
            signal_key: Signal identifier
            
        Returns:
            RGB color tuple
        """
        if signal_key in self.signal_colors:
            return self.signal_colors[signal_key]
            
        # Assign a color from the predefined list if possible
        if len(self.signal_colors) < len(self.COLORS):
            new_color = self.COLORS[len(self.signal_colors)]
        else:
            # Generate a new color dynamically using HSV
            hue = (len(self.signal_colors) * 37) % 360
            hsv_color = pg.hsvColor(hue / 360.0, 1.0, 1.0)
            new_color = hsv_color.getRgb()[:3]
            
        self.signal_colors[signal_key] = new_color
        return new_color
        
    def _show_context_menu(self, position):
        """
        Show a context menu for plot operations.
        
        Args:
            position: Position where the menu should be shown
        """
        context_menu = QtWidgets.QMenu(self)
        
        # Add actions
        clear_action = context_menu.addAction("Clear Plot")
        clear_action.triggered.connect(self.clear_signals)
        
        autoscale_action = context_menu.addAction("Auto Scale")
        autoscale_action.triggered.connect(self.autoscale)
        
        # Add export action
        export_action = context_menu.addAction("Export as Image")
        export_action.triggered.connect(self.export_plot)
        
        # Add cursor toggle if in plot mode
        if self.mode == "plot":
            cursor_action = context_menu.addAction("Toggle Cursors")
            cursor_action.triggered.connect(self.toggle_cursors)
        
        # Add a submenu for removing individual signals if there are any
        if self.signal_keys_assigned:
            remove_menu = context_menu.addMenu("Remove Signal")
            
            for key in sorted(self.signal_keys_assigned):
                action = remove_menu.addAction(key)
                action.triggered.connect(lambda checked=False, key=key: self.remove_signal(key))
        
        # Show the menu
        context_menu.exec(self.mapToGlobal(position))
        
    def clear_signals(self):
        """Remove all signals from the plot."""
        # Keep a copy of keys since we'll be modifying the set during iteration
        signals_to_remove = list(self.signal_keys_assigned)
        for key in signals_to_remove:
            self.remove_signal(key)
    
    def autoscale(self):
        """Autoscale the plot axes to fit all data."""
        self.plot_widget.autoRange()
    
    def process_text_size_edit(self):
        """Process text size edit field value change."""
        try:
            new_size = int(self.text_size_edit.text())
            new_size = max(10, min(50, new_size))
        except ValueError:
            new_size = self.display_text_size
            
        self.update_display_text_size(new_size)
        
    def update_display_text_size(self, new_size):
        """Update display text size and refresh styles for display widgets."""
        self.display_text_size = new_size
        
        # Update TX widgets
        for signal_key, (container, name_label, input_field) in self.tx_widgets.items():
            name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
            input_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
            
        # Update RX widgets
        for signal_key, (container, name_label, output_field) in self.rx_widgets.items():
            name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
            output_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
        
    def export_plot(self):
        """Export the current plot as an image."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Plot", "", "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        
        if filename:
            # Create an exporter for the plot
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(filename)

    # --- Cursor functionality ---
            
    def toggle_cursors(self):
        """Toggle cursor visibility in plot mode."""
        if self.mode != "plot":
            return
            
        self.cursors_active = not self.cursors_active
        
        if self.cursors_active:
            if self.cursor1 is None:
                self.initialize_cursors()
            else:
                self.show_cursors()
            # Update button appearance
            self.cursor_button.setStyleSheet(
                "background-color: rgba(0, 120, 215, 255); color: white; border-radius: 10px; font-weight: bold;"
            )
        else:
            self.hide_cursors()
            # Update button appearance
            self.cursor_button.setStyleSheet(
                "background-color: rgba(0, 120, 215, 150); color: white; border-radius: 10px; font-weight: bold;"
            )
            
    def initialize_cursors(self):
        """Create cursor lines and measurement display."""
        # Create vertical cursor lines
        self.cursor1 = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('r', width=2), label='C1')
        self.cursor2 = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('b', width=2), label='C2')
        
        # Add cursor lines to plot
        self.plot_widget.addItem(self.cursor1)
        self.plot_widget.addItem(self.cursor2)
        
        # Position cursors at 1/3 and 2/3 of the visible range
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        x_span = x_range[1] - x_range[0]
        self.cursor1.setValue(x_range[0] + x_span / 3)
        self.cursor2.setValue(x_range[0] + 2 * x_span / 3)
        
        # Store the relative positions of the cursors in the view (0.0 to 1.0)
        self.cursor1_rel_pos = 1/3
        self.cursor2_rel_pos = 2/3
        
        # Create cursor info label with improved visibility
        self.cursor_info_label = QtWidgets.QLabel(self)
        self.cursor_info_label.setStyleSheet(
            "background-color: rgba(30, 30, 30, 220); color: white; border: 1px solid #555; "
            "border-radius: 5px; padding: 5px; font-weight: bold;"
        )
        self.cursor_info_label.move(10, 35)
        self.cursor_info_label.setFixedWidth(200)
        self.cursor_info_label.show()
        
        # Create cursor link combo box with improved visibility
        self.cursor_link_combo = QtWidgets.QComboBox(self)
        self.cursor_link_combo.setStyleSheet(
            "background-color: rgba(30, 30, 30, 220); color: white; border: 1px solid #555; "
            "border-radius: 5px; padding: 2px; selection-background-color: #0078d7;"
        )
        self.cursor_link_combo.move(10, 120)  # Positioned lower
        self.cursor_link_combo.setFixedWidth(180)
        self.update_cursor_link_options()
        self.cursor_link_combo.currentIndexChanged.connect(self.update_cursor_link)
        self.cursor_link_combo.show()
        
        # Connect cursor signals
        self.cursor1.sigPositionChanged.connect(self.on_cursor1_moved)
        self.cursor2.sigPositionChanged.connect(self.on_cursor2_moved)
        
        # Connect plot's viewRange changed signal to update cursor positions
        self.plot_widget.getViewBox().sigXRangeChanged.connect(self.update_cursor_positions)
        
        # Initial update of cursor info
        self.update_cursor_info()
        
    def on_cursor1_moved(self):
        """Update relative position when cursor 1 is moved by user."""
        if self.cursor1 is not None:
            x_range = self.plot_widget.getViewBox().viewRange()[0]
            x_span = x_range[1] - x_range[0]
            
            # Calculate relative position (0.0 to 1.0)
            if x_span > 0:
                self.cursor1_rel_pos = (self.cursor1.value() - x_range[0]) / x_span
            
            self.update_cursor_info()
            
    def on_cursor2_moved(self):
        """Update relative position when cursor 2 is moved by user."""
        if self.cursor2 is not None:
            x_range = self.plot_widget.getViewBox().viewRange()[0]
            x_span = x_range[1] - x_range[0]
            
            # Calculate relative position (0.0 to 1.0)
            if x_span > 0:
                self.cursor2_rel_pos = (self.cursor2.value() - x_range[0]) / x_span
                
            self.update_cursor_info()
            
    def update_cursor_positions(self, *args):
        """Update cursor positions based on their relative positions when view changes."""
        if not self.cursors_active or self.cursor1 is None:
            return
            
        # Get current view range
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        x_span = x_range[1] - x_range[0]
        
        # Update cursor positions based on their relative positions
        # Block signals temporarily to avoid infinite recursion
        self.cursor1.blockSignals(True)
        self.cursor2.blockSignals(True)
        
        self.cursor1.setValue(x_range[0] + x_span * self.cursor1_rel_pos)
        self.cursor2.setValue(x_range[0] + x_span * self.cursor2_rel_pos)
        
        self.cursor1.blockSignals(False)
        self.cursor2.blockSignals(False)
        
        # Update the cursor info
        self.update_cursor_info()
        
    def show_cursors(self):
        """Show existing cursor elements."""
        if self.cursor1 is not None:
            self.cursor1.show()
            self.cursor2.show()
            self.cursor_info_label.show()
            self.cursor_link_combo.show()
            self.update_cursor_link_options()
            self.update_cursor_info()
            
    def hide_cursors(self):
        """Hide cursor elements without deleting them."""
        if self.cursor1 is not None:
            self.cursor1.hide()
            self.cursor2.hide()
            self.cursor_info_label.hide()
            self.cursor_link_combo.hide()
            
    def remove_cursors(self):
        """Remove cursor elements completely."""
        if self.cursor1 is not None:
            self.plot_widget.removeItem(self.cursor1)
            self.plot_widget.removeItem(self.cursor2)
            self.cursor1 = None
            self.cursor2 = None
        
        if self.cursor_info_label is not None:
            self.cursor_info_label.deleteLater()
            self.cursor_info_label = None
            
        if self.cursor_link_combo is not None:
            self.cursor_link_combo.deleteLater()
            self.cursor_link_combo = None
            
        self.cursor_linked_signal = None
        
    def update_cursor_link_options(self):
        """Update the options in the cursor link combo box."""
        if self.cursor_link_combo is None:
            return
            
        current_linked = self.cursor_linked_signal
        
        self.cursor_link_combo.blockSignals(True)
        self.cursor_link_combo.clear()
        self.cursor_link_combo.addItem("Not linked")
        
        # Add all signals to the combo box
        for i, signal in enumerate(sorted(self.signal_keys_assigned), 1):
            try:
                from telemetry_gui.data.signals import get_signal_name
                signal_name = get_signal_name(signal)
            except ImportError:
                signal_name = signal
                
            self.cursor_link_combo.addItem(signal_name)
            
            # Store the signal key as user data
            self.cursor_link_combo.setItemData(i, signal)
            
            # If this was the previously linked signal, select it
            if signal == current_linked:
                self.cursor_link_combo.setCurrentIndex(i)
                
        self.cursor_link_combo.blockSignals(False)
        
    def update_cursor_link(self, index):
        """Update the variable linked to cursors."""
        if index == 0:
            self.cursor_linked_signal = None
        else:
            # Get the signal key stored as user data
            self.cursor_linked_signal = self.cursor_link_combo.itemData(index)
            
        self.update_cursor_info()
        
    def update_cursor_info(self):
        """Update cursor measurement information."""
        if not self.cursors_active or self.cursor1 is None or not self.cursor1.isVisible():
            return
            
        t1 = self.cursor1.value()
        t2 = self.cursor2.value()
        delta_t = t2 - t1
        
        v1 = None
        v2 = None
        delta_v = None
        
        # Find values at cursor positions if linked to a signal
        if (self.cursor_linked_signal and self.data_manager and 
            self.cursor_linked_signal in self.data_manager.data_history):
            
            # Get data for the linked signal
            data = self.data_manager.data_history[self.cursor_linked_signal]
            if data:
                # Find closest data points to cursor positions
                if len(data) > 0:
                    # Find value at cursor1
                    closest_idx1 = min(range(len(data)), key=lambda i: abs(data[i][1] - t1))
                    v1 = data[closest_idx1][0]
                    
                    # Find value at cursor2
                    closest_idx2 = min(range(len(data)), key=lambda i: abs(data[i][1] - t2))
                    v2 = data[closest_idx2][0]
                    
                    delta_v = v2 - v1
                    
        # Build the information text with highlighted values
        info_text = []
        info_text.append(f"<span style='color:#ff5555;'>t1:</span> {t1:.3f}s")
        if v1 is not None:
            info_text[0] += f", <span style='color:#ff5555;'>v1:</span> {v1:.3f}"
            
        info_text.append(f"<span style='color:#5555ff;'>t2:</span> {t2:.3f}s")
        if v2 is not None:
            info_text[1] += f", <span style='color:#5555ff;'>v2:</span> {v2:.3f}"
            
        info_text.append(f"<span style='color:#55ff55;'>Δt:</span> {delta_t:.3f}s")
        if delta_v is not None:
            info_text[2] += f", <span style='color:#55ff55;'>Δv:</span> {delta_v:.3f}"
            
        # Add rate of change if we have both delta_t and delta_v
        if delta_v is not None and delta_t != 0:
            rate = delta_v / delta_t
            info_text.append(f"<span style='color:#ffaa55;'>Rate:</span> {rate:.3f}/s")
            
        # Update the label with HTML formatting
        self.cursor_info_label.setText("<br>".join(info_text))
        self.cursor_info_label.adjustSize()
        
    def get_state(self):
        """
        Get the current state of the plot for saving/restoring.
        
        Returns:
            Dictionary with plot state
        """
        geom = self.geometry().getRect()
        state = {
            "geometry": {"x": geom[0], "y": geom[1], "width": geom[2], "height": geom[3]},
            "signal_keys": list(self.signal_keys_assigned),
            "mode": self.mode
        }
        
        if self.mode == "display":
            state["text_size"] = self.display_text_size
        elif self.mode in ["plot", "xy"]:
            try:
                time_window = float(self.time_window_edit.text())
            except ValueError:
                time_window = 0
            state["time_window"] = time_window
            
        # Add cursor state if active
        if self.cursors_active and self.cursor1 is not None:
            state["cursors_active"] = True
            state["cursor1_rel_pos"] = self.cursor1_rel_pos
            state["cursor2_rel_pos"] = self.cursor2_rel_pos
            state["cursor_linked_signal"] = self.cursor_linked_signal
        else:
            state["cursors_active"] = False
            
        return state
        
    def set_state(self, state):
        """
        Restore plot state from a saved state dictionary.
        
        Args:
            state: Dictionary with plot state
        """
        # Restore signals
        if "signal_keys" in state:
            for signal_key in state["signal_keys"]:
                self.add_signal(signal_key)
                
        # Restore mode
        if "mode" in state:
            # First get to plot mode
            while self.mode != "plot":
                self.toggle_mode()
                
            # Then toggle to desired mode
            while self.mode != state["mode"]:
                self.toggle_mode()
                
        # Restore time window
        if "time_window" in state:
            self.time_window_edit.setText(str(state["time_window"]))
                
        # Restore text size for display mode
        if "text_size" in state:
            self.display_text_size = state["text_size"]
            self.text_size_edit.setText(str(self.display_text_size))
            self.update_display_text_size(self.display_text_size)
            
        # Restore cursors
        if "cursors_active" in state and state["cursors_active"]:
            self.cursors_active = True
            if self.mode == "plot":
                self.initialize_cursors()
                
                # Restore cursor positions
                if "cursor1_rel_pos" in state:
                    self.cursor1_rel_pos = state["cursor1_rel_pos"]
                if "cursor2_rel_pos" in state:
                    self.cursor2_rel_pos = state["cursor2_rel_pos"]
                    
                # Restore linked signal
                if "cursor_linked_signal" in state:
                    self.cursor_linked_signal = state["cursor_linked_signal"]
                    self.update_cursor_link_options()
                    
                # Update positions and info
                self.update_cursor_positions()
        
    def dragEnterEvent(self, event):
        """Handle drag enter event for drag and drop."""
        # Accept drag events that have the right format
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle drop event for drag and drop."""
        # Process dropped text
        signal_key = event.mimeData().text()
        if signal_key:
            self.add_signal(signal_key)
            self.update_plot()