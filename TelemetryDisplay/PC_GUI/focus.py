# global_focus.py
class FocusManager:
    active_widget = None

    @classmethod
    def set_active(cls, widget):
        # If a different widget was active, clear its active style.
        if cls.active_widget is not None and cls.active_widget != widget:
            cls.active_widget.selected = False
            cls.active_widget.setStyleSheet("QGroupBox { border: 2px solid gray; }")
        cls.active_widget = widget
        if widget is not None:
            widget.selected = True
            widget.setStyleSheet("QGroupBox { border: 2px solid blue; }")

    @classmethod
    def clear_active(cls, widget):
        # Only clear if the widget losing focus is currently active.
        if cls.active_widget == widget:
            widget.selected = False
            widget.setStyleSheet("QGroupBox { border: 2px solid gray; }")
            cls.active_widget = None

    @classmethod
    def get_active(cls):
        return cls.active_widget
