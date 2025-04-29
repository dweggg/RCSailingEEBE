"""
Focus Manager Module
===================

Provides focus management to track the active widget in the application.
"""

from typing import Optional, Any


class FocusManager:
    """
    Static class to manage UI widget focus across the application.
    Tracks which widget is currently "active" for operations like
    adding signals to plots.
    """
    
    _active_widget = None
    
    @classmethod
    def set_active(cls, widget: Any) -> None:
        """
        Set a widget as the active one and update styling accordingly.
        
        Args:
            widget: The widget to be set as active
        """
        # If a different widget was active, clear its active style
        if cls._active_widget is not None and cls._active_widget != widget:
            cls._active_widget.selected = False
            cls._active_widget.setStyleSheet("QGroupBox { border: 2px solid gray; }")
            
        # Set the new active widget
        cls._active_widget = widget
        if widget is not None:
            widget.selected = True
            widget.setStyleSheet("QGroupBox { border: 2px solid blue; }")
    
    @classmethod
    def clear_active(cls, widget: Any) -> None:
        """
        Clear the active state if the widget is currently active.
        
        Args:
            widget: The widget to check and clear if active
        """
        # Only clear if the widget losing focus is currently active
        if cls._active_widget == widget:
            widget.selected = False
            widget.setStyleSheet("QGroupBox { border: 2px solid gray; }")
            cls._active_widget = None
    
    @classmethod
    def get_active(cls) -> Optional[Any]:
        """
        Get the currently active widget.
        
        Returns:
            The active widget or None if no widget is active
        """
        return cls._active_widget