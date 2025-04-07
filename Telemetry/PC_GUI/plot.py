import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from signals import get_signal_name, get_signal_direction  # Import only the required functions
from focus import FocusManager  # Expects a FocusManager class
from uart import send_signal
from data import data_history, start_time
import time
from comm import comm

class DynamicPlot(QtWidgets.QWidget):
    selected_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, tiling_area=None):  
        super().__init__(parent)
        self.tiling_area = tiling_area  
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.signal_keys_assigned = []  
        self.curves = {}
        self.display_text_size = 24  # Moved assignment before init_ui()
        self.init_ui()
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px solid gray;")
        # Instead of a boolean flag, use a string: "plot", "display", or "xy"
        self.mode = "plot"  

        # Persistent widgets for display mode:
        # For TX signals, a container with a signal name label and an editable QLineEdit.
        self.tx_widgets = {}
        # For RX signals, a container with a signal name label and a read-only QLineEdit.
        self.rx_widgets = {}
        # To store the last sent value for TX signals.
        self.last_tx_values = {}

        self.signal_colors = {}  # New dictionary to map signal to color.

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create the plot widget with grid.
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAcceptDrops(False)
        self.plot.viewport().setAcceptDrops(False)
        # Create the legend.
        self.legend = self.plot.addLegend(offset=(10, 10))
        self.legend.anchor = (0, 0)
        self.layout.addWidget(self.plot)

        # Create a QLineEdit to input time window (in seconds) inside the plot.
        self.time_window_edit = QtWidgets.QLineEdit(self.plot)
        self.time_window_edit.setPlaceholderText("Time Window (s)")
        self.time_window_edit.setFixedWidth(100)
        self.time_window_edit.setStyleSheet(
            "background-color: rgba(200, 200, 200, 150); border: 1px solid gray; border-radius: 5px;"
        )
        self.time_window_edit.editingFinished.connect(self.update_plot)

        # Remove button.
        self.remove_button = QtWidgets.QPushButton("X")
        self.remove_button.setParent(self)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.move(self.width() - 25, 5)
        self.remove_button.setStyleSheet(
            "background-color: rgba(255, 0, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.remove_button.clicked.connect(self.remove_self)

        # Toggle mode button.
        # This button now cycles through three modes: plot, display, and xy.
        self.toggle_button = QtWidgets.QPushButton("P")
        self.toggle_button.setFixedSize(40, 20)
        self.toggle_button.setStyleSheet(
            "background-color: rgba(0, 255, 0, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.toggle_button.setParent(self)
        self.toggle_button.move(self.width() - 70, 5)

        # NEW: Cursor toggle button.
        self.cursor_button = QtWidgets.QPushButton("C", self)
        self.cursor_button.setFixedSize(40, 20)
        self.cursor_button.setStyleSheet(
            "background-color: rgba(0, 0, 255, 150); color: white; border-radius: 10px; font-weight: bold;"
        )
        self.cursor_button.move(self.width() - 120, 5)
        self.cursor_button.clicked.connect(self.toggle_cursors)

        # Create display container with a top control for text size.
        self.display_container = QtWidgets.QWidget(self)
        # Replace previous self.display_layout with a new container layout.
        self.display_container_layout = QtWidgets.QVBoxLayout(self.display_container)
        self.display_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a small QLineEdit for text size instead:
        self.text_size_edit = QtWidgets.QLineEdit(self.display_container)
        self.text_size_edit.setPlaceholderText("Text Size")
        self.text_size_edit.setFixedWidth(50)
        self.text_size_edit.setStyleSheet("background-color: rgba(200, 200, 200, 150); border: 1px solid gray; border-radius: 5px;")
        self.text_size_edit.setText(str(self.display_text_size))
        self.text_size_edit.editingFinished.connect(self.process_text_size_edit)
        
        # Sub-layout for signal display widgets.
        self.widget_display_layout = QtWidgets.QVBoxLayout()
        self.display_container_layout.addLayout(self.widget_display_layout)
        
        self.display_container.hide()  
        self.layout.addWidget(self.display_container)

        # NEW: Initialize cursor functionality (invisible by default)
        self.cursors_active = False
        pen_cursor = pg.mkPen('c', width=1, style=QtCore.Qt.PenStyle.DashLine)
        self.cursor1_v = pg.InfiniteLine(angle=90, movable=True, pen=pen_cursor)
        self.cursor1_h = pg.InfiniteLine(angle=0, movable=True, pen=pen_cursor)
        self.cursor2_v = pg.InfiniteLine(angle=90, movable=True, pen=pen_cursor)
        self.cursor2_h = pg.InfiniteLine(angle=0, movable=True, pen=pen_cursor)
        self.cursor1_v.hide(); self.cursor1_h.hide()
        self.cursor2_v.hide(); self.cursor2_h.hide()
        self.plot.addItem(self.cursor1_v)
        self.plot.addItem(self.cursor1_h)
        self.plot.addItem(self.cursor2_v)
        self.plot.addItem(self.cursor2_h)
        self.cursor_info = pg.TextItem("", anchor=(0,0))
        self.cursor_info.hide()
        self.plot.addItem(self.cursor_info)
        self.cursor1_v.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor1_h.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor2_v.sigPositionChanged.connect(self.update_cursor_info)
        self.cursor2_h.sigPositionChanged.connect(self.update_cursor_info)

    def remove_self(self):
        """Safely remove itself from TilingArea."""
        if self.tiling_area:
            self.tiling_area.remove_plot(self)

    def resizeEvent(self, event):
        """Update remove and toggle button positions when resizing the plot."""
        super().resizeEvent(event)
        self.remove_button.move(self.width() - 25, 5)
        self.toggle_button.move(self.width() - 70, 5)
        self.cursor_button.move(self.width() - 120, 5)
        # New: reposition time_window_edit and text_size_edit to bottom-right corners
        margin = 10
        self.time_window_edit.move(self.plot.width() - self.time_window_edit.width() - margin,
                                   self.plot.height() - self.time_window_edit.height() - margin)
        if self.display_container.isVisible():
            self.text_size_edit.move(self.display_container.width() - self.text_size_edit.width() - margin,
                                     self.display_container.height() - self.text_size_edit.height() - margin)
            self.text_size_edit.raise_()

    def add_signal(self, signal):

        if self.mode != "xy":
            """Adds a new signal stream to the plot if not already present."""
            if signal in self.signal_keys_assigned:
                return  
            
            self.signal_keys_assigned.append(signal)
            color = self.get_color(signal)
            curve = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=signal)
            self.curves[signal] = curve

            # If in display mode, add the corresponding display widget.
            if self.mode == "display":
                self.add_display_widget(signal)

    def add_display_widget(self, signal):
        """Add a display widget for a newly added signal based on its direction."""
        if get_signal_direction(signal) == 'TX':
            if signal not in self.tx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(get_signal_name(signal) + ": ")
                name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                editable_input = QtWidgets.QLineEdit()
                editable_input.setPlaceholderText(f"Enter {signal} value...")
                editable_input.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                editable_input.returnPressed.connect(
                    lambda signal=signal, input_field=editable_input: self.on_return_pressed(signal, input_field)
                )
                h_layout.addWidget(editable_input)
                self.tx_widgets[signal] = (container, name_label, editable_input)
                self.widget_display_layout.addWidget(container)  # Use new sub-layout.
        else:
            if signal not in self.rx_widgets:
                container = QtWidgets.QWidget()
                container.setStyleSheet("border: none;")
                h_layout = QtWidgets.QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                name_label = QtWidgets.QLabel(get_signal_name(signal) + ": ")
                name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(name_label)
                
                output_field = QtWidgets.QLineEdit()
                output_field.setReadOnly(True)
                output_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
                h_layout.addWidget(output_field)
                self.rx_widgets[signal] = (container, name_label, output_field)
                self.widget_display_layout.addWidget(container)

    def remove_signal(self, signal):
        """Removes an existing signal stream from the plot."""
        if signal in self.signal_keys_assigned:
            self.signal_keys_assigned.remove(signal)
            if signal in self.curves:
                curve = self.curves.pop(signal)
                self.plot.removeItem(curve)

            # Remove display widgets.
            if signal in self.tx_widgets:
                widget = self.tx_widgets.pop(signal)[0]
                widget.deleteLater()
            if signal in self.rx_widgets:
                widget = self.rx_widgets.pop(signal)[0]
                widget.deleteLater()

    def update_legend(self):
        """Updates the legend based on the current signal streams,
           but only updates once per second.
        """
        current_time = time.time() - start_time
        # Initialize the last update time if it doesn't exist.
        if not hasattr(self, "last_legend_update"):
            self.last_legend_update = 0

        # Only update the legend if 1 second has passed.
        if current_time - self.last_legend_update < 1.0:
            return

        self.last_legend_update = current_time

        # Create the legend once if necessary.
        if not hasattr(self, "legend") or self.legend is None:
            self.legend = self.plot.addLegend(offset=(10, 10))
            self.legend.anchor = (0, 0)
        self.legend.clear()

        # In 'plot' mode, show the signal name with the 1s datarate.
        if self.mode == "plot":
            for signal in self.signal_keys_assigned:
                if signal in self.curves:
                    signal_data = data_history.get(signal, [])
                    count = 0
                    # Iterate backward; stop once data is older than 1 second.
                    for _, t in reversed(signal_data):
                        if t >= current_time - 1:
                            count += 1
                        else:
                            break
                    label = f"{get_signal_name(signal)} ({count} Hz)"
                    self.legend.addItem(self.curves[signal], label)
        else:
            # In other modes, simply display the signal name.
            for signal in self.signal_keys_assigned:
                if signal in self.curves:
                    self.legend.addItem(self.curves[signal], get_signal_name(signal))

    def get_color(self, signal):
        """Return a color for the signal. If not assigned, generate and store a new color."""
        if signal in self.signal_colors:
            return self.signal_colors[signal]

        # Predefined base colors.
        base_colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 165, 0),
            (128, 0, 128),
            (0, 255, 255),
            (255, 192, 203)
        ]

        if len(self.signal_colors) < len(base_colors):
            new_color = base_colors[len(self.signal_colors)]
        else:
            # Generate a new color dynamically using HSV.
            hue = (len(self.signal_colors) * 37) % 360
            hsv_color = pg.hsvColor(hue / 360.0, 1.0, 1.0)
            new_color = hsv_color.getRgb()[:3]
        self.signal_colors[signal] = new_color
        return new_color
            
    def update_plot(self, data_history=data_history):
        """Updates the plot based on the current mode."""
        if self.mode == "xy":
            self.update_xy_plot()
            return
        elif self.mode == "display":
            self.update_display_widgets(data_history)
            return

        # For regular time-series mode.
        self.update_legend()
        current_time = time.time() - start_time

        for signal in self.signal_keys_assigned:
            signal_data = data_history.get(signal)
            if signal_data:
                # Append a new entry if the last update is older than 500ms.
                last_value, last_timestamp = signal_data[-1]
                if current_time - last_timestamp >= 0.5:
                    signal_data.append((last_value, current_time))

                # Instead of two list comprehensions, unpack once.
                try:
                    # signal_data contains (value, timestamp) pairs.
                    vals, ts = zip(*signal_data)
                except ValueError:
                    # signal_data is empty; skip updating.
                    continue
                # Set data with times on the x-axis and signal values on the y-axis.
                self.curves[signal].setData(list(ts), list(vals))

        try:
            time_window = float(self.time_window_edit.text())
        except ValueError:
            time_window = 0

        if time_window > 0:
            self.plot.setXRange(max(0, current_time - time_window), current_time)
        else:
            self.plot.enableAutoRange(axis='x')

    def update_xy_plot(self):
        """Updates the XY plot using the first signal as x-axis and the second as y-axis."""
        if len(self.signal_keys_assigned) < 2:
            return
        
        x_signal = self.signal_keys_assigned[0]
        y_signal = self.signal_keys_assigned[1]
        current_time = time.time() - start_time
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
        
        if hasattr(self, "xy_curve"):
            self.xy_curve.setData(x_vals, y_vals)
        else:
            self.xy_curve = self.plot.plot(x_vals, y_vals, pen=pg.mkPen(width=2), name="")
        
        if not hasattr(self, "xy_marker"):
            self.xy_marker = pg.ScatterPlotItem(
                size=10, 
                pen=pg.mkPen(None), 
                brush=pg.mkBrush('r')
            )
            self.plot.addItem(self.xy_marker)
        self.xy_marker.setData([x_vals[-1]], [y_vals[-1]])
        
        self.plot.setLabel('bottom', get_signal_name(x_signal))
        self.plot.setLabel('left', get_signal_name(y_signal))

    def update_display_widgets(self, data_history):
        """Update display widget text for each signal."""
        for signal in self.signal_keys_assigned:
            value = None
            if signal in data_history and data_history[signal]:
                value = data_history[signal][-1][0]
            
            if get_signal_direction(signal) == 'TX':
                current_value = self.last_tx_values.get(signal, value)
                container, name_label, input_field = self.tx_widgets[signal]
                if not input_field.hasFocus():
                    input_field.setText(str(current_value) if current_value is not None else "")
            else:
                container, name_label, output_field = self.rx_widgets[signal]
                output_field.setText(str(value) if value is not None else "No data available")

    def mousePressEvent(self, event):
        FocusManager.set_active(self)
        self.selected_signal.emit(self)
        super().mousePressEvent(event)

    def toggle_mode(self):
        """Cycle through three modes: plot, display, and xy."""
        if self.mode == "plot":
            self.mode = "display"
            self.toggle_button.setText("D")
            self.plot.hide()
            self.display_container.show()
            self.remove_button.raise_()
            self.toggle_button.raise_()
            self.cursor_button.raise_()
            # New: bring text_size_edit to the front
            self.text_size_edit.raise_()
            self.populate_display_mode()
        elif self.mode == "display":
            self._backup_signal_keys = list(self.signal_keys_assigned)
            self.mode = "xy"
            self.toggle_button.setText("XY")
            self.display_container.hide()
            self.plot.show()
            # Clear the plot for xy mode.
            self.plot.clear()
            # In xy mode we do not need a legend.
            self.curves = {}
            if len(self._backup_signal_keys) >= 2:
                self.signal_keys_assigned = self._backup_signal_keys[:2]
            else:
                self.signal_keys_assigned = self._backup_signal_keys
            if not hasattr(self, "xy_curve"):
                self.xy_curve = self.plot.plot(pen=pg.mkPen(width=2), name="")
            self.update_xy_plot()
        elif self.mode == "xy":
            self.mode = "plot"
            self.toggle_button.setText("P")
            self.display_container.hide()
            self.plot.show()
            if hasattr(self, "xy_curve"):
                self.plot.removeItem(self.xy_curve)
                del self.xy_curve
            if hasattr(self, "xy_marker"):
                self.plot.removeItem(self.xy_marker)
                del self.xy_marker
            if hasattr(self, "_backup_signal_keys"):
                self.signal_keys_assigned = self._backup_signal_keys
                del self._backup_signal_keys
            # Clear the plot and reinitialize the legend.
            self.plot.clear()
            self.legend = self.plot.addLegend(offset=(10, 10))
            self.legend.anchor = (0, 0)
            self.curves = {}
            for signal in self.signal_keys_assigned:
                color = self.get_color(signal)
                self.curves[signal] = self.plot.plot(pen=pg.mkPen(color=color, width=2), name=get_signal_name(signal))
            self.plot.setLabel('bottom', "")
            self.plot.setLabel('left', "")
            self.update_plot()

    def populate_display_mode(self):
        """(Re)populate the display layout with persistent widgets for each signal."""
        # Clear previous widgets.
        while self.widget_display_layout.count():
            item = self.widget_display_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for signal in self.signal_keys_assigned:
            if get_signal_direction(signal) == 'TX':
                if signal not in self.tx_widgets:
                    self.add_display_widget(signal)
                else:
                    self.widget_display_layout.addWidget(self.tx_widgets[signal][0])
            else:
                if signal not in self.rx_widgets:
                    self.add_display_widget(signal)
                else:
                    self.widget_display_layout.addWidget(self.rx_widgets[signal][0])
        self.update_display_widgets(data_history)

    def on_return_pressed(self, signal, input_field):
        """Handles Enter key press: converts text to float, updates data, and flashes the input field."""
        try:
            new_value = float(input_field.text())
        except ValueError:
            return

        send_signal(comm, signal, new_value)
        if signal not in data_history:
            data_history[signal] = []
        data_history[signal].append((new_value, time.time() - start_time))
        self.last_tx_values[signal] = new_value
        input_field.setStyleSheet("background-color: green; font-size: 24px; font-weight: bold;")
        QtCore.QTimer.singleShot(150, lambda: input_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;"))
        print(f"Updated {signal} with value: {new_value}")

    def clear_layout(self, layout):
        """Clear all items from the layout."""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def get_state(self):
        geom = self.geometry().getRect()
        state = {
            "geometry": {"x": geom[0], "y": geom[1], "width": geom[2], "height": geom[3]},
            "signal_keys": self.signal_keys_assigned,
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
        return state

    def toggle_cursors(self):
        self.cursors_active = not self.cursors_active
        if self.cursors_active:
            self.cursor1_v.show(); self.cursor1_h.show()
            self.cursor2_v.show(); self.cursor2_h.show()
            self.cursor_info.show()
            # Set initial positions based on current view range.
            x_bounds = self.plot.viewRange()[0]
            y_bounds = self.plot.viewRange()[1]
            self.cursor1_v.setValue(x_bounds[0])
            self.cursor2_v.setValue(x_bounds[1])
            self.cursor1_h.setValue(y_bounds[0])
            self.cursor2_h.setValue(y_bounds[1])
            self.update_cursor_info()
        else:
            self.cursor1_v.hide(); self.cursor1_h.hide()
            self.cursor2_v.hide(); self.cursor2_h.hide()
            self.cursor_info.hide()

    def update_display_text_size(self, new_size):
        """Update display text size and refresh styles for display widgets."""
        self.display_text_size = new_size
        # Update TX widgets.
        for signal, (container, name_label, input_field) in self.tx_widgets.items():
            name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
            input_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
        # Update RX widgets.
        for signal, (container, name_label, output_field) in self.rx_widgets.items():
            name_label.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")
            output_field.setStyleSheet(f"font-size: {self.display_text_size}px; font-weight: bold;")

    def update_cursor_info(self):
        # Retrieve positions.
        t1 = self.cursor1_v.value()
        t2 = self.cursor2_v.value()
        y1 = self.cursor1_h.value()
        y2 = self.cursor2_h.value()
        delta_t = abs(t2 - t1)
        delta_y = abs(y2 - y1)
        info_text = f"t1: {t1:.3f}, t2: {t2:.3f}, Δt: {delta_t:.3f}\n" \
                    f"y1: {y1:.3f}, y2: {y2:.3f}, Δy: {delta_y:.3f}"
        self.cursor_info.setText(info_text)
        # Position info text near the upper left cursor.
        self.cursor_info.setPos(t1, y2)

    def process_text_size_edit(self):
        try:
            new_size = int(self.text_size_edit.text())
            new_size = max(10, min(50, new_size))
        except ValueError:
            new_size = self.display_text_size
        self.update_display_text_size(new_size)
