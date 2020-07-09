"""sr.robot3 - Student Robotics API for Python 3."""

from j5.boards.sr.v4 import PowerOutputPosition
from j5.components.motor import MotorSpecialState
from j5.components.piezo import Note

from .logging import logger_setup
from .robot import Robot, __version__

logger_setup()

COAST = MotorSpecialState.COAST
BRAKE = MotorSpecialState.BRAKE

OUT_H0 = PowerOutputPosition.H0
OUT_H1 = PowerOutputPosition.H1
OUT_L0 = PowerOutputPosition.L0
OUT_L1 = PowerOutputPosition.L1
OUT_L2 = PowerOutputPosition.L2
OUT_L3 = PowerOutputPosition.L3

__all__ = [
    "__version__",
    "BRAKE",
    "COAST",
    "OUT_H0",
    "OUT_H1",
    "OUT_L0",
    "OUT_L1",
    "OUT_L2",
    "OUT_L3",
    "Note",
    "Robot",
]
