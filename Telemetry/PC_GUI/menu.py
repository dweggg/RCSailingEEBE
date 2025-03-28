from PyQt6 import QtWidgets, QtCore, QtGui
import json

def export_layout(main_window, tiling_area):
    """Exports the current layout state to a JSON file."""
    state = tiling_area.get_layout_state()
    filename, _ = QtWidgets.QFileDialog.getSaveFileName(
        main_window,
        "Export Layout",
        "",
        "JSON Files (*.json)"
    )
    if filename:
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=4)
            QtWidgets.QMessageBox.information(main_window, "Export Layout", "Layout exported successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(main_window, "Error", f"Failed to export layout: {e}")

def import_layout(main_window, tiling_area):
    """Imports a layout state from a JSON file and reconfigures the tiling area."""
    filename, _ = QtWidgets.QFileDialog.getOpenFileName(
        main_window,
        "Import Layout",
        "",
        "JSON Files (*.json)"
    )
    if filename:
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            tiling_area.apply_layout_state(state)
            QtWidgets.QMessageBox.information(main_window, "Import Layout", "Layout imported successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(main_window, "Error", f"Failed to import layout: {e}")

def setup_menu_bar(main_window, tiling_area):
    """
    Set up the menu bar for main_window with actions:
      - Import Layout
      - Export Layout
      - Import Variables
    """
    menu_bar = main_window.menuBar()
    
    # --- Layout Menu ---
    layout_menu = menu_bar.addMenu("Layout")
    
    import_layout_action = QtGui.QAction("Import Layout", main_window)
    import_layout_action.triggered.connect(lambda: import_layout(main_window, tiling_area))
    layout_menu.addAction(import_layout_action)
    
    export_layout_action = QtGui.QAction("Export Layout", main_window)
    export_layout_action.triggered.connect(lambda: export_layout(main_window, tiling_area))
    layout_menu.addAction(export_layout_action)
    
