"""Mock and test fixtures."""
import pytest

from sr.robot3 import Robot
from sr.robot3.env import CONSOLE_ENVIRONMENT_WITH_VISION


@pytest.fixture
def robot() -> Robot:
    """A robot object that does not observe the global lock."""
    Robot._obtain_lock = lambda _: None  # type: ignore
    return Robot(auto_start=True, env=CONSOLE_ENVIRONMENT_WITH_VISION)
