"""sr.robot3 Robot class."""

import logging
from argparse import ArgumentParser
from pathlib import Path
from stat import S_ISFIFO
from typing import Dict, List, Optional

from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version
from j5.boards import Board, BoardGroup
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard
from j5.boards.sr.v4.ruggeduino import Ruggeduino
from serial.tools.list_ports_common import ListPortInfo

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
            ignored_ruggeduinos: Optional[List[str]] = None,
    ) -> None:
        self._auto_start = auto_start
        self._verbose = verbose
        self._environment = env

        if verbose:
            LOGGER.setLevel(logging.DEBUG)

        self._parse_arguments()

        if ignored_ruggeduinos is None:
            self._ignored_ruggeduino_serials = []
        else:
            self._ignored_ruggeduino_serials = ignored_ruggeduinos

        LOGGER.info(f"sr.robot3 version {__version__}")
        LOGGER.debug("Verbose mode enabled.")
        LOGGER.debug(f"j5 version {j5_version}")
        LOGGER.debug(f"Environment: {self._environment.name}")

        self._init_power_board()
        self._init_auxilliary_boards()

        self._init_ruggeduinos()

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

    def _init_ruggeduinos(self) -> None:
        """
        Initialise the ruggeduinos.

        Ignore any that the user has specified.
        """
        self.ignored_ruggeduinos: Dict[str, str] = {}

        ruggeduino_backend = self._environment.get_backend(Ruggeduino)

        class IgnoredRuggeduinoBackend(ruggeduino_backend):  # type: ignore
            """A backend that ignores some ruggeduinos."""

            @classmethod
            def is_arduino(cls, port: ListPortInfo) -> bool:
                """Check if a ListPortInfo represents a valid Arduino derivative."""
                if port.serial_number in self._ignored_ruggeduino_serials:
                    self.ignored_ruggeduinos[port.serial_number] = port.device
                    return False
                return super().is_arduino(port)  # type: ignore

        self.ruggeduinos = BoardGroup.get_board_group(
            Ruggeduino,
            IgnoredRuggeduinoBackend,
        )

    def _log_discovered_boards(self) -> None:
        """Log all boards that we have discovered."""
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name} - {board.serial_number}")
            LOGGER.debug(
                f"Firmware Version of {board.serial_number}: {board.firmware_version}",
            )

    def _parse_arguments(self) -> None:
        """Parse arguments to the program."""
        parser = ArgumentParser(description="Robot Usercode Program")
        parser.add_argument(
            "--usbkey",
            type=Path,
            help="The path of the (non-volatile) user USB key",
        )
        parser.add_argument(
            "--startfifo",
            type=Path,
            help="The named pipe which start info will be received through",
        )
        args = parser.parse_args()

        self._usbkey: Optional[Path] = None

        if args.usbkey:
            if args.usbkey.exists() and args.usbkey.is_dir():
                self._usbkey = args.usbkey
                LOGGER.debug(f"USBkey is at {self._usbkey}")
            else:
                LOGGER.warn("Invalid usbkey supplied as argument")

        self._startfifo: Optional[Path] = None

        if args.startfifo:
            if args.startfifo.exists() and S_ISFIFO(args.startfifo.stat().st_mode):
                self._startfifo = args.startfifo
                LOGGER.debug(f"StartFIFO is at {self._startfifo}")
            else:
                LOGGER.warn("Invalid StartFIFO supplied as argument")

    @property
    def motor_board(self) -> MotorBoard:
        """
        Get the motor board.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.motor_boards.singular()

    @property
    def ruggeduino(self) -> Ruggeduino:
        """
        Get the ruggeduino.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.ruggeduinos.singular()

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
    def usbkey(self) -> Optional[Path]:
        """The path of the USB code drive."""
        return self._usbkey

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
