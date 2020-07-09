"""Environment definitions."""

from j5.backends import Environment
from j5.backends.console.sr.v4 import (
    SRV4MotorBoardConsoleBackend,
    SRV4PowerBoardConsoleBackend,
    SRV4ServoBoardConsoleBackend,
)
from j5.backends.hardware.sr.v4 import (
    SRV4MotorBoardHardwareBackend,
    SRV4PowerBoardHardwareBackend,
    SRV4ServoBoardHardwareBackend,
)

__all__ = [
    "HARDWARE_ENVIRONMENT",
    "CONSOLE_ENVIRONMENT",
]

HARDWARE_ENVIRONMENT = Environment("Hardware Environment")

HARDWARE_ENVIRONMENT.register_backend(SRV4PowerBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4ServoBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4MotorBoardHardwareBackend)

CONSOLE_ENVIRONMENT = Environment("Console Environment")

CONSOLE_ENVIRONMENT.register_backend(SRV4PowerBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4ServoBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4MotorBoardConsoleBackend)
