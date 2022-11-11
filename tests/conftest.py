"""Mock and test fixtures."""
import pytest

from sr.robot3 import Robot
from sr.robot3.env import CONSOLE_ENVIRONMENT_WITH_VISION


@pytest.fixture
def robot() -> Robot:
    """A robot object."""
    return Robot(auto_start=True, env=CONSOLE_ENVIRONMENT_WITH_VISION)
