"""
UI Module
=======

Provides user interface components for the telemetry application.
"""

from telemetry_gui.ui.focus_manager import FocusManager
from telemetry_gui.ui.logger_widget import CSVLoggerWidget, TerminalLogWidget
from telemetry_gui.ui.plot_widget import DynamicPlot
from telemetry_gui.ui.tiling_area import TilingArea
from telemetry_gui.ui.menu_system import setup_menu_system, MenuSystem

__all__ = [
    'FocusManager',
    'CSVLoggerWidget',
    'TerminalLogWidget',
    'DynamicPlot',
    'TilingArea',
    'setup_menu_system',
    'MenuSystem'
]