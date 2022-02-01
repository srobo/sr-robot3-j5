"""Environment definitions."""

from j5.backends import Environment
from j5.backends.console.sr.v4 import (
    SRV4MotorBoardConsoleBackend,
    SRV4PowerBoardConsoleBackend,
    SRV4RuggeduinoConsoleBackend,
    SRV4ServoBoardConsoleBackend,
)
from j5.backends.hardware.sr.v4 import (
    SRV4MotorBoardHardwareBackend,
    SRV4PowerBoardHardwareBackend,
    SRV4RuggeduinoHardwareBackend,
    SRV4ServoBoardHardwareBackend,
)

__all__ = [
    "HARDWARE_ENVIRONMENT",
    "CONSOLE_ENVIRONMENT",
]

from sr.robot3.vision import SRZolotoHardwareBackend

HARDWARE_ENVIRONMENT = Environment("Hardware Environment")

HARDWARE_ENVIRONMENT.register_backend(SRV4PowerBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4ServoBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4MotorBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4RuggeduinoHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRZolotoHardwareBackend)

CONSOLE_ENVIRONMENT = Environment("Console Environment")

CONSOLE_ENVIRONMENT.register_backend(SRV4PowerBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4ServoBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4MotorBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4RuggeduinoConsoleBackend)

CONSOLE_ENVIRONMENT_WITH_VISION = Environment("Console Environment with Vision")

CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4PowerBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4ServoBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4MotorBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4RuggeduinoConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRZolotoHardwareBackend)
