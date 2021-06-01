"""sr.robot3 Robot class."""

import asyncio
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from astoria.common.messages.astmetad import Metadata, RobotMode
from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version
from j5.boards import Board, BoardGroup
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard
from j5.boards.sr.v4.ruggeduino import Ruggeduino
from j5.components.piezo import Note
from serial.tools.list_ports_common import ListPortInfo

from .astoria import GetMetadataConsumer, WaitForStartButtonBroadcastConsumer
from .env import HARDWARE_ENVIRONMENT
from .timeout import kill_after_delay

__version__ = "2021.0.0a1.dev1"

LOGGER = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


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

        if ignored_ruggeduinos is None:
            self._ignored_ruggeduino_serials = []
        else:
            self._ignored_ruggeduino_serials = ignored_ruggeduinos

        LOGGER.info(f"sr.robot3 version {__version__}")
        LOGGER.debug("Verbose mode enabled.")
        LOGGER.debug(f"j5 version {j5_version}")
        LOGGER.debug(f"Environment: {self._environment.name}")

        self._init_metadata()

        self._init_power_board()
        self._init_auxilliary_boards()

        # self._init_ruggeduinos()

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

    def _init_metadata(self) -> None:
        """Fetch metadata from Astoria."""
        self._metadata, self._code_path = GetMetadataConsumer.get_metadata()

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
    def metadata(self) -> Metadata:
        """Get all metadata."""
        return self._metadata

    @property
    def arena(self) -> str:
        """Determine the arena of the robot."""
        return self.metadata.arena

    @property
    def mode(self) -> RobotMode:
        """Determine the mode of the robot."""
        return self.metadata.mode

    @property
    def usbkey(self) -> Optional[Path]:
        """The path of the USB code drive."""
        return self._code_path

    @property
    def zone(self) -> int:
        """The arena zone that the robot starts in."""
        return self.metadata.zone

    def wait_start(self) -> None:
        """
        Wait for a start signal.

        Intended for use with `Robot(auto_start=False)`, to allow
        students to run code and setup their robot before the start
        of a match.

        Currently implemented to be compatible with herdsman.
        """
        LOGGER.info("Waiting for start signal")

        astoria_start = WaitForStartButtonBroadcastConsumer(self._verbose, None)
        flash_loop = True

        async def wait_for_physical_start() -> None:
            self.power_board.piezo.buzz(timedelta(seconds=0.1), Note.A6)
            counter = 0
            led_state = False
            while not self.power_board.start_button.is_pressed and flash_loop:
                if counter % 6 == 0:
                    led_state = not led_state
                    self.power_board._run_led.state = led_state
                await asyncio.sleep(0.05)
                counter += 1
            # Turn on the LED now that we are starting
            self.power_board._run_led.state = True

        loop.run_until_complete(
            asyncio.wait(
                [
                    astoria_start.run(),
                    wait_for_physical_start(),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            ),
        )

        flash_loop = False  # Stop the flashing loop

        # Reload metadata as a metadata USB may have been inserted.
        # This ensures that the game timeout is observed even if the metadata
        # USB is inserted after usercode execution begins.
        self._init_metadata()

        LOGGER.info("Start signal received; continuing.")

        if self._metadata.game_timeout is not None:
            LOGGER.info(f"Game length set to {self._metadata.game_timeout}s")
            kill_after_delay(self._metadata.game_timeout)
