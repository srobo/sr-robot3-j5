"""sr.robot3 Robot class."""

import logging

from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version

from .env import HardwareEnvironment

__version__ = "2021.0.0a0.dev0"

LOGGER = logging.getLogger(__name__)


class Robot(BaseRobot):
    """
    Student Robotics robot.

    Inherits from j5 BaseRobot to ensure that all boards are made safe
    in the event of a crash, and to ensure that there is only one instance
    of this class on a given machine.
    """

    def __init__(
            self,
            *,
            auto_start: bool = True,
            verbose: bool = False,
            env: Environment = HardwareEnvironment
    ) -> None:
        self._auto_start = auto_start
        self._verbose = verbose
        self._environment = env
        if verbose:
            LOGGER.setLevel(logging.DEBUG)

        LOGGER.info(f"sr.robot3 version {__version__}")
        LOGGER.debug("Verbose mode enabled.")
        LOGGER.debug(f"j5 version {j5_version}")
        LOGGER.debug(f"Environment: {self._environment.name}")

        # Enumerate hardware here

        if auto_start:
            LOGGER.debug("Auto start is enabled.")
            self.wait_start()
        else:
            LOGGER.debug("Auto start is disabled.")

    def wait_start(self) -> None:
        """
        Wait for a start signal.

        Intended for use with `Robot(auto_start=False)`, to allow
        students to run code and setup their robot before the start
        of a match.
        """
        LOGGER.info("Waiting for start signal")

        raise NotImplementedError()
        LOGGER.info("Start signal received; continuing.")
