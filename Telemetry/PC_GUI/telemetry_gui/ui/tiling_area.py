"""
Tiling Area Module
================

Provides a layout manager for arranging multiple plots in a grid pattern.
"""

import json
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from PyQt6 import QtWidgets, QtCore

from telemetry_gui.ui.plot_widget import DynamicPlot


class TilingArea(QtWidgets.QWidget):
    """
    Widget that manages a grid layout of plots with support for 
    adding/removing rows and columns, splitting plots, and saving layouts.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the tiling area.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # References to data and communication managers (set by caller)
        self.data_manager = None
        self.comm_manager = None
        
        # Track all plots in this format: {plot_widget: (row, col)}
        self.plots: Dict[DynamicPlot, Tuple[int, int]] = {}
        
        # Create main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # We'll use nested splitters instead of a grid layout
        self.main_splitter = None  # Will be a vertical splitter containing rows
        self.row_splitters = []    # List of horizontal splitters, each representing a row
        
        # Track rows and columns
        self.rows = 0
        self.cols = 0
    
    def add_initial_row(self) -> None:
        """Add the initial row with a single plot."""
        self.add_row(0)
    
    def add_row(self, position: int) -> None:
        """
        Add a new row of plots at the specified position.
        
        Args:
            position: Row index to insert at
        """
        # Create a new horizontal splitter for this row
        row_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        
        # If this is the first row, create the main vertical splitter as well
        if self.main_splitter is None:
            self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
            self.main_layout.addWidget(self.main_splitter)
        
        # Insert the new row splitter at the correct position
        self.main_splitter.insertWidget(position, row_splitter)
        self.row_splitters.insert(position, row_splitter)
        
        # Adjust plot positions to account for inserted row
        plots_to_move = {}
        for plot, (row, col) in list(self.plots.items()):
            if row >= position:
                plots_to_move[plot] = (row + 1, col)
                
        for plot, (new_row, col) in plots_to_move.items():
            self.plots[plot] = (new_row, col)
            
        # Create plots for the new row
        cols = max(1, self.cols if self.rows > 0 else 1)
        for col in range(cols):
            self._add_plot(position, col)
        
        # Update row count
        self.rows += 1
    
    def remove_row(self, row: int) -> None:
        """
        Remove a row of plots.
        
        Args:
            row: Row index to remove
        """
        if row < 0 or row >= self.rows or self.rows <= 1:
            return
            
        # Get the row splitter to remove
        row_splitter = self.row_splitters[row]
        
        # Collect plots in the row to remove
        plots_to_remove = [plot for plot, (r, _) in self.plots.items() if r == row]
        
        # Remove the plots
        for plot in plots_to_remove:
            del self.plots[plot]
            plot.setParent(None)
            plot.deleteLater()
        
        # Remove the row splitter
        row_splitter.setParent(None)
        row_splitter.deleteLater()
        self.row_splitters.pop(row)
        
        # Adjust plot positions for rows after the removed row
        plots_to_move = {}
        for plot, (r, c) in list(self.plots.items()):
            if r > row:
                plots_to_move[plot] = (r - 1, c)
                
        for plot, new_pos in plots_to_move.items():
            self.plots[plot] = new_pos
        
        # Update row count
        self.rows -= 1
    
    def add_column(self, position: int) -> None:
        """
        Add a new column of plots at the specified position.
        
        Args:
            position: Column index to insert at
        """
        if self.rows == 0:
            # No rows yet, add a row first
            self.add_initial_row()
            return
            
        # Adjust plot positions for columns after the inserted column
        plots_to_move = {}
        for plot, (row, col) in list(self.plots.items()):
            if col >= position:
                plots_to_move[plot] = (row, col + 1)
                
        for plot, new_pos in plots_to_move.items():
            self.plots[plot] = new_pos
        
        # Add a plot to each row at the specified column position
        for row in range(self.rows):
            self._add_plot(row, position)
        
        # Update column count
        self.cols += 1
    
    def remove_column(self, col: int) -> None:
        """
        Remove a column of plots.
        
        Args:
            col: Column index to remove
        """
        if col < 0 or col >= self.cols or self.cols <= 1:
            return
            
        # Collect plots in the column to remove
        plots_to_remove = [plot for plot, (_, c) in self.plots.items() if c == col]
        
        # Remove the plots
        for plot in plots_to_remove:
            del self.plots[plot]
            plot.setParent(None)
            plot.deleteLater()
        
        # Adjust plot positions for columns after the removed column
        plots_to_move = {}
        for plot, (r, c) in list(self.plots.items()):
            if c > col:
                plots_to_move[plot] = (r, c - 1)
                
        for plot, new_pos in plots_to_move.items():
            self.plots[plot] = new_pos
        
        # Update column count
        self.cols -= 1
    
    def _add_plot(self, row: int, col: int) -> DynamicPlot:
        """
        Add a plot at the specified grid position.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            The created plot widget
        """
        # Create a DynamicPlot with references to tiling, data and comm managers
        plot = DynamicPlot(
            f"Plot {row+1},{col+1}",
            parent=self,
            tiling_area=self,
            data_manager=self.data_manager,
            comm_manager=self.comm_manager
        )
        
        # Ensure the row exists
        if row >= len(self.row_splitters):
            self.add_row(row)
            
        # Get the row splitter
        row_splitter = self.row_splitters[row]
        
        # Insert the plot at the correct column position
        if col < row_splitter.count():
            # Need to insert at a specific position
            # Create a temporary widget as placeholder
            temp = QtWidgets.QWidget()
            row_splitter.insertWidget(col, temp)
            temp.setParent(None)  # Remove the temporary widget
            # Now insert our plot at the same position
            row_splitter.insertWidget(col, plot)
        else:
            # Can just add to the end
            row_splitter.addWidget(plot)
        
        # Store the plot's position
        self.plots[plot] = (row, col)
        
        # Even out the sizes
        sizes = [1 for _ in range(row_splitter.count())]
        row_splitter.setSizes(sizes)
        
        # Update counts for correct tracking
        self.rows = max(self.rows, row + 1)
        self.cols = max(self.cols, col + 1)
        
        return plot
    
    def split_horizontal(self, plot: DynamicPlot) -> Optional[DynamicPlot]:
        """
        Split a plot horizontally (add a column after it).
        
        Args:
            plot: Plot widget to split
            
        Returns:
            The newly created plot or None if split failed
        """
        if plot not in self.plots:
            return None
            
        row, col = self.plots[plot]
        self.add_column(col + 1)
        
        # Return the new plot that was created next to it
        for p, (r, c) in self.plots.items():
            if r == row and c == col + 1:
                return p
                
        return None
    
    def split_vertical(self, plot: DynamicPlot) -> Optional[DynamicPlot]:
        """
        Split a plot vertically (add a row after it).
        
        Args:
            plot: Plot widget to split
            
        Returns:
            The newly created plot or None if split failed
        """
        if plot not in self.plots:
            return None
            
        row, col = self.plots[plot]
        self.add_row(row + 1)
        
        # Return the new plot that was created below it
        for p, (r, c) in self.plots.items():
            if r == row + 1 and c == col:
                return p
                
        return None
    
    def merge_right(self, plot: DynamicPlot) -> bool:
        """
        Merge a plot with the one to its right.
        
        Args:
            plot: Plot to merge
            
        Returns:
            True if successful, False otherwise
        """
        if plot not in self.plots:
            return False
            
        row, col = self.plots[plot]
        if col + 1 >= self.cols:
            return False
            
        # Find the plot to the right
        right_plot = None
        for p, (r, c) in self.plots.items():
            if r == row and c == col + 1:
                right_plot = p
                break
                
        if not right_plot:
            return False
            
        # Transfer signals from right plot to this one
        for signal_key in list(right_plot.signal_keys_assigned):
            # Skip signals that are already in the target plot
            if signal_key not in plot.signal_keys_assigned:
                plot.add_signal(signal_key)
        
        # Remove the right plot column
        self.remove_column(col + 1)
        
        return True
    
    def merge_down(self, plot: DynamicPlot) -> bool:
        """
        Merge a plot with the one below it.
        
        Args:
            plot: Plot to merge
            
        Returns:
            True if successful, False otherwise
        """
        if plot not in self.plots:
            return False
            
        row, col = self.plots[plot]
        if row + 1 >= self.rows:
            return False
            
        # Find the plot below
        bottom_plot = None
        for p, (r, c) in self.plots.items():
            if r == row + 1 and c == col:
                bottom_plot = p
                break
                
        if not bottom_plot:
            return False
            
        # Transfer signals from bottom plot to this one
        for signal_key in list(bottom_plot.signal_keys_assigned):
            # Skip signals that are already in the target plot
            if signal_key not in plot.signal_keys_assigned:
                plot.add_signal(signal_key)
        
        # Remove the bottom plot's row
        self.remove_row(row + 1)
        
        return True
    
    def save_layout(self, filename: Optional[str] = None) -> bool:
        """
        Save the current layout configuration to a file.
        
        Args:
            filename: Path to save the layout to, or None to prompt
            
        Returns:
            True if successful, False otherwise
        """
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Layout", "", "JSON Files (*.json)"
            )
            
        if not filename:
            return False
            
        layout_data = {
            "rows": self.rows,
            "cols": self.cols,
            "plots": []
        }
        
        # Export each plot's position and assigned signals
        for plot, (row, col) in self.plots.items():
            plot_data = {
                "row": row,
                "col": col,
                "signals": list(plot.signal_keys_assigned)
            }
            layout_data["plots"].append(plot_data)
            
        try:
            with open(filename, 'w') as f:
                json.dump(layout_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving layout: {e}")
            return False
    
    def load_layout(self, filename: Optional[str] = None) -> bool:
        """
        Load a layout configuration from a file.
        
        Args:
            filename: Path to load the layout from, or None to prompt
            
        Returns:
            True if successful, False otherwise
        """
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Load Layout", "", "JSON Files (*.json)"
            )
            
        if not filename or not Path(filename).exists():
            return False
            
        try:
            with open(filename, 'r') as f:
                layout_data = json.load(f)
                
            # Clear existing layout
            self.clear_layout()
                
            # Create the grid structure
            rows = layout_data.get("rows", 0)
            cols = layout_data.get("cols", 0)
            
            # Create empty grid
            for r in range(rows):
                self.add_row(r)
                for c in range(cols):
                    if c > 0:  # First column already added with the row
                        self._add_plot(r, c)
            
            # Apply signals to plots
            for plot_data in layout_data.get("plots", []):
                row = plot_data.get("row", 0)
                col = plot_data.get("col", 0)
                signals = plot_data.get("signals", [])
                
                # Find the corresponding plot
                target_plot = None
                for plot, (r, c) in self.plots.items():
                    if r == row and c == col:
                        target_plot = plot
                        break
                
                if target_plot:
                    # Add each signal to the plot
                    for signal in signals:
                        target_plot.add_signal(signal)
            
            return True
        except Exception as e:
            print(f"Error loading layout: {e}")
            return False
    
    def clear_layout(self) -> None:
        """Clear all plots and reset the layout."""
        # Remove all plots
        for plot in list(self.plots.keys()):
            plot.setParent(None)
            plot.deleteLater()
            
        # Clean up splitters
        if self.main_splitter:
            self.main_splitter.setParent(None)
            self.main_splitter.deleteLater()
            self.main_splitter = None
            
        # Clean up row splitters
        for splitter in self.row_splitters:
            splitter.setParent(None)
            splitter.deleteLater()
        self.row_splitters.clear()
        
        # Reset tracking variables
        self.plots.clear()
        self.rows = 0
        self.cols = 0