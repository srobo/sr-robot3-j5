"""Data types used in the API."""

from enum import Enum


class RobotMode(Enum):
    """Mode of the robot."""

    COMP = "comp"
    DEV = "dev"
