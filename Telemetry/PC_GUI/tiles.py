from PyQt6 import QtWidgets, QtCore
from plot import DynamicPlot
from focus import FocusManager

class TilingArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        # Outer splitter to hold rows (each row is a horizontal splitter).
        self.rows_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.rows_splitter.setChildrenCollapsible(False)

        self.selected_plot = None
        # Mapping: DynamicPlot -> (row, col)
        self.plots = {}  

        # Main layout: toolbar on top then the rows splitter.
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.init_toolbar()
        self.main_layout.addLayout(self.toolbar)
        self.main_layout.addWidget(self.rows_splitter)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # List to track horizontal splitters (each row).
        self.row_splitters = []
        self.add_initial_row()  # Start with one row containing one plot

    def init_toolbar(self):
        self.toolbar = QtWidgets.QHBoxLayout()
        self.add_left_btn = QtWidgets.QPushButton("Add Left")
        self.add_right_btn = QtWidgets.QPushButton("Add Right")
        self.add_top_btn = QtWidgets.QPushButton("Add Top")
        self.add_bottom_btn = QtWidgets.QPushButton("Add Bottom")
        self.toolbar.addWidget(self.add_left_btn)
        self.toolbar.addWidget(self.add_right_btn)
        self.toolbar.addWidget(self.add_top_btn)
        self.toolbar.addWidget(self.add_bottom_btn)
        
        self.add_left_btn.clicked.connect(lambda: self.add_plot_relative("left"))
        self.add_right_btn.clicked.connect(lambda: self.add_plot_relative("right"))
        self.add_top_btn.clicked.connect(lambda: self.add_plot_relative("top"))
        self.add_bottom_btn.clicked.connect(lambda: self.add_plot_relative("bottom"))

    def update_plot_positions(self):
        """Rebuilds the mapping of plots to their (row, col) positions."""
        self.plots.clear()
        for row_index, row_splitter in enumerate(self.row_splitters):
            for col_index in range(row_splitter.count()):
                widget = row_splitter.widget(col_index)
                if isinstance(widget, DynamicPlot):
                    self.plots[widget] = (row_index, col_index)

    def add_initial_row(self):
        """Creates a new horizontal splitter row and adds an initial plot."""
        row_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        row_splitter.setChildrenCollapsible(False)
        self.row_splitters.append(row_splitter)
        self.rows_splitter.addWidget(row_splitter)
        self.add_plot_to_row(row_splitter)


    def add_plot_to_row(self, row_splitter, position=None):
        """Adds a new DynamicPlot to a given row splitter."""
        plot = DynamicPlot(tiling_area=self)  # Pass the tiling area to the plot
        plot.selected_signal.connect(self.set_selected_plot)
        plot.remove_button.clicked.connect(lambda: self.remove_plot(plot))
        self.selected_plot = plot
        FocusManager.set_active(plot)

        if position is None:
            row_splitter.addWidget(plot)
        else:
            # To "insert" into QSplitter, rebuild the list of widgets.
            widgets = [row_splitter.widget(i) for i in range(row_splitter.count())]
            row_splitter.hide()
            for w in widgets:
                w.setParent(None)
            new_widgets = []
            for i, w in enumerate(widgets):
                if i == position:
                    new_widgets.append(plot)
                new_widgets.append(w)
            if position >= len(widgets):
                new_widgets.append(plot)
            for w in new_widgets:
                row_splitter.addWidget(w)
            row_splitter.show()
        self.update_plot_positions()
        self.set_selected_plot(plot)

    def add_plot_relative(self, direction):
        """Adds a plot relative to the currently selected plot in the given direction."""
        if self.selected_plot is None:
            # If no plot is selected, start a new row.
            self.add_initial_row()
            return
        
        row, col = self.plots[self.selected_plot]
        if direction == "right":
            row_splitter = self.row_splitters[row]
            self.add_plot_to_row(row_splitter, position=col+1)
        elif direction == "left":
            row_splitter = self.row_splitters[row]
            self.add_plot_to_row(row_splitter, position=col)
        elif direction == "top":
            # Insert a new row above the selected plot's row.
            new_row_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            new_row_splitter.setChildrenCollapsible(False)
            self.rows_splitter.insertWidget(row, new_row_splitter)
            self.row_splitters.insert(row, new_row_splitter)
            self.add_plot_to_row(new_row_splitter)
            self.update_plot_positions()
        elif direction == "bottom":
            # Insert a new row below the selected plot's row.
            new_row_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            new_row_splitter.setChildrenCollapsible(False)
            insert_index = row + 1
            self.rows_splitter.insertWidget(insert_index, new_row_splitter)
            self.row_splitters.insert(insert_index, new_row_splitter)
            self.add_plot_to_row(new_row_splitter)
            self.update_plot_positions()

        else:
            return

    def remove_plot(self, plot):
        """Removes the given plot widget."""
        if plot not in self.plots:
            return
        row, _ = self.plots[plot]
        plot.setParent(None)
        self.update_plot_positions()
        if self.selected_plot == plot:
            self.selected_plot = None

    def set_selected_plot(self, plot):
        """Highlights the selected plot and un-highlights the previous one."""
        if self.selected_plot is not None:
            self.selected_plot.setStyleSheet("border: 2px solid gray;")
        self.selected_plot = plot
        self.selected_plot.setStyleSheet("border: 2px solid blue;")

    def get_layout_state(self):
        """
        Returns a dictionary capturing the layout state, including:
         - Each row's list of plots (with their geometry, assigned sensor keys, and mode)
         - The positions (row, col) of each plot
        """
        layout_state = {"rows": []}
        for row_index, row_splitter in enumerate(self.row_splitters):
            row_state = {"plots": []}
            for col_index in range(row_splitter.count()):
                widget = row_splitter.widget(col_index)
                if hasattr(widget, "get_state"):
                    plot_state = widget.get_state()
                    # Include the row and column for clarity.
                    plot_state["position"] = {"row": row_index, "col": col_index}
                    row_state["plots"].append(plot_state)
            layout_state["rows"].append(row_state)
        return layout_state

    def apply_layout_state(self, layout_state):

        FocusManager.clear_active(FocusManager.get_active())
        self.selected_plot = None
        
        # Remove existing rows and clear the splitter.
        for row_splitter in self.row_splitters:
            row_splitter.setParent(None)
        self.row_splitters.clear()
        self.rows_splitter.hide()
        while self.rows_splitter.count():
            widget = self.rows_splitter.widget(0)
            widget.setParent(None)
        self.rows_splitter.show()
        
        # Rebuild layout from the state.
        for row in layout_state.get("rows", []):
            new_row_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            new_row_splitter.setChildrenCollapsible(False)
            self.row_splitters.append(new_row_splitter)
            self.rows_splitter.addWidget(new_row_splitter)
            for plot_state in row.get("plots", []):
                # Create a new DynamicPlot.
                plot = DynamicPlot(tiling_area=self)
                # Restore assigned sensor keys.
                for sensor in plot_state.get("sensor_keys", []):
                    plot.add_sensor(sensor)
                # Restore display mode if necessary.
                if plot_state.get("display_mode", "plot") == "display" and not plot.display_mode:
                    plot.toggle_mode()
                # Connect signals.
                plot.selected_signal.connect(self.set_selected_plot)
                plot.remove_button.clicked.connect(lambda p=plot: self.remove_plot(p))
                new_row_splitter.addWidget(plot)

        self.update_plot_positions()