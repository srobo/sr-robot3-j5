"""sr.robot3 Robot class."""

import logging

from j5 import BaseRobot, BoardGroup, Environment
from j5.boards import Board
from j5 import __version__ as j5_version
from j5.boards.sr.v4 import PowerBoard, MotorBoard, ServoBoard

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

        self._init_power_board()

        self._list_discovered_boards()

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
        self._power_boards = BoardGroup.get_board_group(
            PowerBoard,
            self._environment.get_backend(PowerBoard),
        )
        self.power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _log_discovered_boards(self) -> None:
        """Log all boards that we have discovered."""
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name} - {board.serial}")
            LOGGER.debug(f"Firmware Version of {board.serial}: {board.firmware_version}")

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
