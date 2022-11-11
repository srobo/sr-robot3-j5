"""Test the Robot object."""
import math
import time

from sr.robot3 import Robot


def test_time(robot: Robot) -> None:
    """Test that the time function works."""
    assert math.isclose(robot.time(), time.time())
