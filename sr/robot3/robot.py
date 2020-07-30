"""sr.robot3 Robot class."""

import logging
from pathlib import Path

from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version
from j5.boards import Board
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard

from .env import HARDWARE_ENVIRONMENT
from .types import RobotMode

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
            env: Environment = HARDWARE_ENVIRONMENT,
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

        self._init_power_board()
        self._init_auxilliary_boards()

        self._log_discovered_boards()

        if auto_start:
            LOGGER.debug("Auto start is enabled.")
            self.wait_start()
        else:
            LOGGER.debug("Auto start is disabled.")

    def _init_power_board(self) -> None:
        """
        Find and initialise the power board.

        The power board is is the only required board.
        """
        self._power_boards = self._environment.get_board_group(PowerBoard)
        self.power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _init_auxilliary_boards(self) -> None:
        """Find and initialise auxilliary boards."""
        self.motor_boards = self._environment.get_board_group(MotorBoard)
        self.servo_boards = self._environment.get_board_group(ServoBoard)

    def _log_discovered_boards(self) -> None:
        """Log all boards that we have discovered."""
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name} - {board.serial_number}")
            LOGGER.debug(
                f"Firmware Version of {board.serial_number}: {board.firmware_version}",
            )

    @property
    def motor_board(self) -> MotorBoard:
        """
        Get the motor board.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.motor_boards.singular()

    @property
    def servo_board(self) -> ServoBoard:
        """
        Get the servo board.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.servo_boards.singular()

    @property
    def mode(self) -> RobotMode:
        """Determine the mode of the robot."""
        raise NotImplementedError()

    @property
    def usbkey(self) -> Path:
        """The path of the USB code drive."""
        raise NotImplementedError()

    @property
    def zone(self) -> int:
        """The arena zone that the robot starts in."""
        raise NotImplementedError()

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
