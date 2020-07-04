"""Environment definitions."""
from typing import Type, cast

from j5.backends import Backend, Environment
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
    "HardwareEnvironment",
]

HardwareEnvironment = Environment("Hardware Environment")

HardwareEnvironment.register_backend(cast(Type[Backend], SRV4PowerBoardHardwareBackend))
HardwareEnvironment.register_backend(cast(Type[Backend], SRV4ServoBoardHardwareBackend))
HardwareEnvironment.register_backend(cast(Type[Backend], SRV4MotorBoardHardwareBackend))

ConsoleEnvironment = Environment("Console Environment")

ConsoleEnvironment.register_backend(cast(Type[Backend], SRV4PowerBoardConsoleBackend))
ConsoleEnvironment.register_backend(cast(Type[Backend], SRV4ServoBoardConsoleBackend))
ConsoleEnvironment.register_backend(cast(Type[Backend], SRV4MotorBoardConsoleBackend))
