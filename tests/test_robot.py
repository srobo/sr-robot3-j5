"""Test the Robot object."""
import math
import time
from unittest.mock import patch

from sr.robot3 import Robot


def test_time(robot: Robot) -> None:
    """Test that the time function works."""
    assert math.isclose(robot.time(), time.time())


def test_sleep(robot: Robot) -> None:
    """Test that the sleep function sleeps."""
    with patch('time.sleep', return_value=None) as patched_time_sleep:
        robot.sleep(0.4)
        patched_time_sleep.assert_called_once_with(0.4)
