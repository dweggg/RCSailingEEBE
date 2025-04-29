"""
Communication Module
=================

Manages communication protocols for telemetry data.
"""

from telemetry_gui.communication.comm_manager import (
    CommunicationProtocol,
    SerialProtocol,
    CommunicationManager
)

__all__ = ['CommunicationProtocol', 'SerialProtocol', 'CommunicationManager']