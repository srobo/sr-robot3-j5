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

from j5_zoloto import ZolotoSingleHardwareBackend

from sr.robot3.vision import SRZolotoSingleHardwareBackend

HARDWARE_ENVIRONMENT = Environment("Hardware Environment")

HARDWARE_ENVIRONMENT.register_backend(SRV4PowerBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4ServoBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4MotorBoardHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRV4RuggeduinoHardwareBackend)
HARDWARE_ENVIRONMENT.register_backend(SRZolotoSingleHardwareBackend)

CONSOLE_ENVIRONMENT = Environment("Console Environment")

CONSOLE_ENVIRONMENT.register_backend(SRV4PowerBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4ServoBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4MotorBoardConsoleBackend)
CONSOLE_ENVIRONMENT.register_backend(SRV4RuggeduinoConsoleBackend)

VISION_ONLY_ENVIRONMENT = Environment("Console Environment")

VISION_ONLY_ENVIRONMENT.register_backend(SRV4PowerBoardConsoleBackend)
VISION_ONLY_ENVIRONMENT.register_backend(SRV4ServoBoardConsoleBackend)
VISION_ONLY_ENVIRONMENT.register_backend(SRV4MotorBoardConsoleBackend)
VISION_ONLY_ENVIRONMENT.register_backend(SRV4RuggeduinoConsoleBackend)
VISION_ONLY_ENVIRONMENT.register_backend(SRZolotoSingleHardwareBackend)

