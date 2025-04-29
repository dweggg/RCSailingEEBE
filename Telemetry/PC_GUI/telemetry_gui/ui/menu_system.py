"""
Menu System Module
================

Provides menu functionality for the telemetry application.
"""

from PyQt6 import QtWidgets, QtCore, QtGui
from typing import Optional, Callable

from telemetry_gui.ui.tiling_area import TilingArea
from telemetry_gui.ui.focus_manager import FocusManager
from telemetry_gui.ui.plot_widget import DynamicPlot


class MenuSystem:
    """Class for managing application menus and actions."""
    
    def __init__(self, main_window: QtWidgets.QMainWindow, tiling_area: TilingArea = None):
        """
        Initialize the menu system.
        
        Args:
            main_window: Main application window
            tiling_area: Tiling area widget for plot management
        """
        self.main_window = main_window
        self.tiling_area = tiling_area
        self.menu_bar = main_window.menuBar()
        
        # Create menus
        self._create_file_menu()
        self._create_layout_menu()
        self._create_plot_menu()
        self._create_help_menu()
    
    def _create_file_menu(self) -> None:
        """Create the File menu."""
        file_menu = self.menu_bar.addMenu("&File")
        
        # New action
        new_action = QtGui.QAction("&New", self.main_window)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_layout)
        file_menu.addAction(new_action)
        
        # Load layout action
        load_action = QtGui.QAction("&Load Layout", self.main_window)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_layout)
        file_menu.addAction(load_action)
        
        # Save layout action
        save_action = QtGui.QAction("&Save Layout", self.main_window)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_layout)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Export plot action
        export_action = QtGui.QAction("Export &Plot", self.main_window)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_active_plot)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QtGui.QAction("E&xit", self.main_window)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)
    
    def _create_layout_menu(self) -> None:
        """Create the Layout menu."""
        layout_menu = self.menu_bar.addMenu("&Layout")
        
        # Add row actions
        row_menu = layout_menu.addMenu("&Row")
        
        add_row_action = QtGui.QAction("&Add Row", self.main_window)
        add_row_action.triggered.connect(lambda: self._add_row())
        row_menu.addAction(add_row_action)
        
        add_row_before_action = QtGui.QAction("Add Row &Before Selected", self.main_window)
        add_row_before_action.triggered.connect(self._add_row_before_selected)
        row_menu.addAction(add_row_before_action)
        
        add_row_after_action = QtGui.QAction("Add Row &After Selected", self.main_window)
        add_row_after_action.triggered.connect(self._add_row_after_selected)
        row_menu.addAction(add_row_after_action)
        
        remove_row_action = QtGui.QAction("&Remove Selected Row", self.main_window)
        remove_row_action.triggered.connect(self._remove_selected_row)
        row_menu.addAction(remove_row_action)
        
        # Add column actions
        col_menu = layout_menu.addMenu("&Column")
        
        add_col_action = QtGui.QAction("&Add Column", self.main_window)
        add_col_action.triggered.connect(lambda: self._add_column())
        col_menu.addAction(add_col_action)
        
        add_col_before_action = QtGui.QAction("Add Column &Before Selected", self.main_window)
        add_col_before_action.triggered.connect(self._add_column_before_selected)
        col_menu.addAction(add_col_before_action)
        
        add_col_after_action = QtGui.QAction("Add Column &After Selected", self.main_window)
        add_col_after_action.triggered.connect(self._add_column_after_selected)
        col_menu.addAction(add_col_after_action)
        
        remove_col_action = QtGui.QAction("&Remove Selected Column", self.main_window)
        remove_col_action.triggered.connect(self._remove_selected_column)
        col_menu.addAction(remove_col_action)
        
        layout_menu.addSeparator()
        
        # Split actions
        split_menu = layout_menu.addMenu("&Split")
        
        split_horizontal_action = QtGui.QAction("Split &Horizontally", self.main_window)
        split_horizontal_action.triggered.connect(self._split_horizontal)
        split_menu.addAction(split_horizontal_action)
        
        split_vertical_action = QtGui.QAction("Split &Vertically", self.main_window)
        split_vertical_action.triggered.connect(self._split_vertical)
        split_menu.addAction(split_vertical_action)
        
        # Merge actions
        merge_menu = layout_menu.addMenu("&Merge")
        
        merge_right_action = QtGui.QAction("Merge &Right", self.main_window)
        merge_right_action.triggered.connect(self._merge_right)
        merge_menu.addAction(merge_right_action)
        
        merge_down_action = QtGui.QAction("Merge &Down", self.main_window)
        merge_down_action.triggered.connect(self._merge_down)
        merge_menu.addAction(merge_down_action)
    
    def _create_plot_menu(self) -> None:
        """Create the Plot menu."""
        plot_menu = self.menu_bar.addMenu("&Plot")
        
        # Clear plot action
        clear_action = QtGui.QAction("&Clear Selected Plot", self.main_window)
        clear_action.triggered.connect(self._clear_selected_plot)
        plot_menu.addAction(clear_action)
        
        # Auto scale action
        autoscale_action = QtGui.QAction("&Auto Scale Selected", self.main_window)
        autoscale_action.triggered.connect(self._autoscale_selected)
        plot_menu.addAction(autoscale_action)
        
        plot_menu.addSeparator()
        
        # Pause/resume updates action (spacebar shortcut handled globally)
        freeze_action = QtGui.QAction("&Pause/Resume Updates", self.main_window)
        freeze_action.setShortcut("Space")
        freeze_action.triggered.connect(self._toggle_freeze)
        plot_menu.addAction(freeze_action)
        
        # Clear all data action
        clear_all_action = QtGui.QAction("Clear &All Data", self.main_window)
        clear_all_action.triggered.connect(self._clear_all_data)
        plot_menu.addAction(clear_all_action)
    
    def _create_help_menu(self) -> None:
        """Create the Help menu."""
        help_menu = self.menu_bar.addMenu("&Help")
        
        # Keyboard shortcuts action
        shortcuts_action = QtGui.QAction("&Keyboard Shortcuts", self.main_window)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        # About action
        about_action = QtGui.QAction("&About", self.main_window)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    # --- File menu handlers ---
    
    def _new_layout(self) -> None:
        """Create a new layout."""
        if not self.tiling_area:
            return
            
        reply = QtWidgets.QMessageBox.question(
            self.main_window, "New Layout",
            "Are you sure you want to clear the current layout?", 
            QtWidgets.QMessageBox.StandardButton.Yes | 
            QtWidgets.QMessageBox.StandardButton.No, 
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.tiling_area.clear_layout()
            self.tiling_area.add_initial_row()
    
    def _load_layout(self) -> None:
        """Load a layout from a file."""
        if not self.tiling_area:
            return
            
        self.tiling_area.load_layout()
    
    def _save_layout(self) -> None:
        """Save the current layout to a file."""
        if not self.tiling_area:
            return
            
        self.tiling_area.save_layout()
    
    def _export_active_plot(self) -> None:
        """Export the active plot as an image."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot):
            QtWidgets.QMessageBox.information(
                self.main_window, "Export Plot",
                "Please select a plot to export first."
            )
            return
            
        active_widget.export_plot()
    
    # --- Layout menu handlers ---
    
    def _add_row(self, position: int = None) -> None:
        """
        Add a row at the given position.
        
        Args:
            position: Row index to insert at, or None to append
        """
        if not self.tiling_area:
            return
            
        if position is None:
            position = self.tiling_area.rows
            
        self.tiling_area.add_row(position)
    
    def _add_row_before_selected(self) -> None:
        """Add a row before the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        row, _ = self.tiling_area.plots[active_widget]
        self.tiling_area.add_row(row)
    
    def _add_row_after_selected(self) -> None:
        """Add a row after the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        row, _ = self.tiling_area.plots[active_widget]
        self.tiling_area.add_row(row + 1)
    
    def _remove_selected_row(self) -> None:
        """Remove the row containing the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        row, _ = self.tiling_area.plots[active_widget]
        self.tiling_area.remove_row(row)
    
    def _add_column(self, position: int = None) -> None:
        """
        Add a column at the given position.
        
        Args:
            position: Column index to insert at, or None to append
        """
        if not self.tiling_area:
            return
            
        if position is None:
            position = self.tiling_area.cols
            
        self.tiling_area.add_column(position)
    
    def _add_column_before_selected(self) -> None:
        """Add a column before the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        _, col = self.tiling_area.plots[active_widget]
        self.tiling_area.add_column(col)
    
    def _add_column_after_selected(self) -> None:
        """Add a column after the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        _, col = self.tiling_area.plots[active_widget]
        self.tiling_area.add_column(col + 1)
    
    def _remove_selected_column(self) -> None:
        """Remove the column containing the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        _, col = self.tiling_area.plots[active_widget]
        self.tiling_area.remove_column(col)
    
    def _split_horizontal(self) -> None:
        """Split the selected plot horizontally."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        self.tiling_area.split_horizontal(active_widget)
    
    def _split_vertical(self) -> None:
        """Split the selected plot vertically."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        self.tiling_area.split_vertical(active_widget)
    
    def _merge_right(self) -> None:
        """Merge the selected plot with the one to its right."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        self.tiling_area.merge_right(active_widget)
    
    def _merge_down(self) -> None:
        """Merge the selected plot with the one below it."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot) or active_widget not in self.tiling_area.plots:
            return
            
        self.tiling_area.merge_down(active_widget)
    
    # --- Plot menu handlers ---
    
    def _clear_selected_plot(self) -> None:
        """Clear all signals from the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot):
            return
            
        active_widget.clear_signals()
    
    def _autoscale_selected(self) -> None:
        """Auto-scale the selected plot."""
        active_widget = FocusManager.get_active()
        if not active_widget or not isinstance(active_widget, DynamicPlot):
            return
            
        active_widget.autoscale()
    
    def _toggle_freeze(self) -> None:
        """Toggle freeze state for plot updates."""
        # This is implemented in the main application class
        # Signal is emitted and we're using space key shortcut
        pass
    
    def _clear_all_data(self) -> None:
        """Clear all data from the application."""
        # This should be implemented by connecting to a signal or callback
        # that can be handled in the main application
        pass
    
    # --- Help menu handlers ---
    
    def _show_shortcuts(self) -> None:
        """Show a dialog with keyboard shortcuts."""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>New layout</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open layout</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save layout</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Export selected plot</td></tr>
        <tr><td><b>Space</b></td><td>Pause/resume updates</td></tr>
        <tr><td><b>Alt+F4</b></td><td>Exit application</td></tr>
        </table>
        <br>
        <b>Focus a plot by clicking on it to select it for operations.</b>
        """
        QtWidgets.QMessageBox.information(self.main_window, "Keyboard Shortcuts", shortcuts_text)
    
    def _show_about(self) -> None:
        """Show the about dialog."""
        about_text = """
        <h3>e-Tech Sailing Telemetry Logger</h3>
        <p>Version 1.0.0</p>
        <p>A telemetry visualization and logging tool for the e-Tech Sailing project.</p>
        <p>© 2025 CITCEA-UPC</p>
        """
        QtWidgets.QMessageBox.about(self.main_window, "About", about_text)


def setup_menu_system(main_window: QtWidgets.QMainWindow, tiling_area: Optional[TilingArea] = None) -> MenuSystem:
    """
    Setup the menu system for the application.
    
    Args:
        main_window: Main application window
        tiling_area: Tiling area widget
        
    Returns:
        The created menu system
    """
    return MenuSystem(main_window, tiling_area)