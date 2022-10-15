"""sr.robot3 Robot class."""

import asyncio
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Type

from astoria.common.metadata import Metadata, RobotMode
from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version
from j5.backends import Backend
from j5.boards import Board, BoardGroup
from j5.boards.sr.v4 import MotorBoard, PowerBoard, Ruggeduino, ServoBoard
from j5.components.piezo import Note
from j5_zoloto import ZolotoCameraBoard, ZolotoHardwareBackend
from serial.tools.list_ports_common import ListPortInfo
from zoloto.cameras.camera import find_camera_ids

from .astoria import GetMetadataConsumer, WaitForStartButtonBroadcastConsumer
from .env import HARDWARE_ENVIRONMENT
from .kch import KCH
from .timeout import kill_after_delay
from .vision import SRZolotoHardwareBackend

__version__ = "2023.0.2"


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
            auto_start: bool = False,
            verbose: bool = False,
            env: Environment = HARDWARE_ENVIRONMENT,
            ignored_ruggeduinos: Optional[List[str]] = None,
    ) -> None:
        """
        Initialise a Robot object.

        :param auto_start: Automatically start the robot ignoring the start
            button, defaults to False.
        :param verbose: Turn on verbose logging, defaults to False.
        :param env: The :class:`j5.backends.environment.Environment` to run the
            Robot under. See :ref:`Environments` for more information.
        :param ignored_ruggeduinos: List of Ruggeduino serial numbers to ignore.
            See :ref:`Custom Ruggeduino Firmware` for more information.
        """
        self._auto_start = auto_start
        self._verbose = verbose
        self._environment = env

        if verbose:
            LOGGER.setLevel(logging.DEBUG)
            os.environ["OPENCV_LOG_LEVEL"] = "DEBUG"
        else:
            os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

        if ignored_ruggeduinos is None:
            self._ignored_ruggeduino_serials = []
        else:
            self._ignored_ruggeduino_serials = ignored_ruggeduinos

        LOGGER.debug("Verbose mode enabled.")
        LOGGER.debug(f"sr.robot3 version {__version__}")
        LOGGER.debug(f"j5 version {j5_version}")
        LOGGER.debug(f"Environment: {self._environment.name}")

        self._init_metadata()

        self._init_cameras(self.metadata.marker_offset)
        self._init_power_board()
        self._init_auxilliary_boards()

        self._init_ruggeduinos()

        self._log_discovered_boards()

        if auto_start:
            LOGGER.debug("Auto start is enabled.")
        else:
            LOGGER.debug("Auto start is disabled.")
            self.wait_start()

    def _init_cameras(self, marker_offset: int) -> None:
        """Initialise vision system for a single camera."""
        backend_class: Type[Backend] = self._environment.get_backend(ZolotoCameraBoard)

        # Override the hardware backend with our custom one
        if backend_class is ZolotoHardwareBackend:
            backend_class = SRZolotoHardwareBackend

        class OffsetZolotoBackend(backend_class):  # type: ignore
            """A zoloto backend, with marker offsets added."""

            @classmethod
            def discover(cls) -> Set[Board]:
                return {
                    ZolotoCameraBoard(
                        str(camera_id),
                        cls(camera_id, marker_offset=marker_offset),
                    )
                    for camera_id in find_camera_ids()
                }

        self._cameras = BoardGroup.get_board_group(
            ZolotoCameraBoard,
            OffsetZolotoBackend,
        )

    def _init_power_board(self) -> None:
        """
        Find and initialise the power board.

        The power board is is the only required board.
        """
        self._power_boards = self._environment.get_board_group(PowerBoard)
        self._power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _init_auxilliary_boards(self) -> None:
        """Find and initialise auxilliary boards."""
        self._kch = KCH()
        self._motor_boards = self._environment.get_board_group(MotorBoard)
        self._servo_boards = self._environment.get_board_group(ServoBoard)

    def _init_ruggeduinos(self) -> None:
        """
        Initialise the ruggeduinos.

        Ignore any that the user has specified.
        """
        self.ignored_ruggeduinos: Dict[str, str] = {}

        ruggeduino_backend: Type[Backend] = self._environment.get_backend(Ruggeduino)

        class IgnoredRuggeduinoBackend(ruggeduino_backend):  # type: ignore
            """A backend that ignores some ruggeduinos."""

            @classmethod
            def is_arduino(cls, port: ListPortInfo) -> bool:
                """Check if a ListPortInfo represents a valid Arduino derivative."""
                if port.serial_number in self._ignored_ruggeduino_serials:
                    self.ignored_ruggeduinos[port.serial_number] = port.device
                    return False
                return super().is_arduino(port)  # type: ignore

        self._ruggeduinos = BoardGroup.get_board_group(
            Ruggeduino,
            IgnoredRuggeduinoBackend,
        )

    def _init_metadata(self) -> None:
        """Fetch metadata from Astoria."""
        self._metadata, self._code_path = GetMetadataConsumer.get_metadata()
        offset = self._metadata.marker_offset
        if hasattr(self, '_cameras'):
            for camera in self._cameras:
                zcam = camera._backend._zcam  # type: ignore[attr-defined]
                zcam._marker_offset = offset

    def _log_discovered_boards(self) -> None:
        """Log all boards that we have discovered."""
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name} - {board.serial_number}")
            LOGGER.debug(
                f"Firmware Version of {board.serial_number}: {board.firmware_version}",
            )

    @property
    def camera(self) -> ZolotoCameraBoard:
        """
        Get the robot's camera interface.

        :returns: a :class:`j5_zoloto.board.ZolotoCameraBoard`.
        """
        return self._cameras.singular()

    @property
    def kch(self) -> KCH:
        """
        Get the KCH.

        :returns: a :class:`KCH`.
        """
        return self._kch

    @property
    def motor_boards(self) -> BoardGroup[MotorBoard, Backend]:
        """
        Get the group of motor boards.

        :returns: a group of :class:`j5.boards.sr.v4.MotorBoard`.
        """
        return self._motor_boards

    @property
    def motor_board(self) -> MotorBoard:
        """
        Get the motor board.

        :returns: a :class:`j5.boards.sr.v4.MotorBoard`.
        :raises j5.backends.CommunicationError: there isn't exactly one
            motor board attached.
        """
        return self._motor_boards.singular()

    @property
    def ruggeduinos(self) -> BoardGroup[Ruggeduino, Backend]:
        """
        Get the group of ruggeduinos.

        :returns: a group of :class:`j5.boards.sr.v4.Ruggeduino`.
        """
        return self._ruggeduinos  # type: ignore

    @property
    def ruggeduino(self) -> Ruggeduino:
        """
        Get the ruggeduino.

        :returns: a :class:`j5.boards.sr.v4.Ruggeduino`.
        :raises j5.backends.CommunicationError: there isn't exactly one
            ruggeduino attached.
        """
        return self._ruggeduinos.singular()

    @property
    def power_board(self) -> PowerBoard:
        """
        Get the power board.

        :returns: a :class:`j5.boards.sr.v4.PowerBoard`.
        :raises j5.backends.CommunicationError: there isn't exactly one
            power board attached.
        """
        return self._power_board

    @property
    def servo_boards(self) -> BoardGroup[ServoBoard, Backend]:
        """
        Get the group of servo boards.

        :returns: a group of :class:`j5.boards.sr.v4.ServoBoard`.
        """
        return self._servo_boards

    @property
    def servo_board(self) -> ServoBoard:
        """
        Get the servo board.

        :returns: a :class:`j5.boards.sr.v4.ServoBoard`.
        :raises j5.backends.CommunicationError: there isn't exactly
            one servo board attached.
        """
        return self._servo_boards.singular()

    @property
    def metadata(self) -> Metadata:
        """
        Get the metadata information object.

        :returns: All available metadata.
        """
        return self._metadata

    @property
    def arena(self) -> str:
        """
        Determine the arena of the robot.

        If the robot is not in a match, this will be ``A``.

        :returns: The arena at the robot is in.
        """
        return self.metadata.arena

    @property
    def mode(self) -> RobotMode:
        """
        Determine the mode of the robot.

        See :ref:`Robot Modes` for available modes.

        :returns: current mode of the robot.
        """
        return self.metadata.mode

    @property
    def usbkey(self) -> Optional[Path]:
        """
        The path of the USB code drive.

        :returns: path to the mountpoint of the USB code drive.
        """
        return self._code_path

    @property
    def zone(self) -> int:
        """
        The arena zone that the robot starts in.

        :returns: arena zone that the robot starts in.
        """
        return self.metadata.zone

    def print_wifi_details(self) -> None:
        """Prints the current WiFi details stored in robot-settings.toml."""
        if not self.metadata.wifi_enabled:
            LOGGER.warn("Could not print WiFi details - WiFi is not enabled")
            return
        LOGGER.info("WiFi credentials:")
        LOGGER.info(f"SSID: {self.metadata.wifi_ssid}")
        LOGGER.info(f"Password: {self.metadata.wifi_psk}")

    def wait_start(self) -> None:
        """
        Wait for a start signal.

        Intended for use with `Robot(auto_start=False)`, to allow
        students to run code and setup their robot before the start
        of a match.
        """
        LOGGER.info("Waiting for start signal")

        start_event = asyncio.Event()

        astoria_start = WaitForStartButtonBroadcastConsumer(
            self._verbose,
            None,  # Don't pass a config
            start_event,
        )

        async def wait_for_physical_start() -> None:
            self.power_board.piezo.buzz(timedelta(seconds=0.1), Note.A6)
            counter = 0
            led_state = False
            _ = self.power_board.start_button.is_pressed
            while not self.power_board.start_button.is_pressed and not start_event.is_set():  # noqa: E501
                if counter % 6 == 0:
                    led_state = not led_state
                    self.power_board._run_led.state = led_state
                    self.kch.start = led_state
                await asyncio.sleep(0.05)
                counter += 1
            start_event.set()
            # Turn on the LED now that we are starting
            self.power_board._run_led.state = True

            # Turn off the KCH Start LED.
            self.kch.start = False

        loop.run_until_complete(
            asyncio.gather(
                astoria_start.run(),
                wait_for_physical_start(),
            ),
        )

        # Reload metadata as a metadata USB may have been inserted.
        # This ensures that the game timeout is observed even if the metadata
        # USB is inserted after usercode execution begins.
        self._init_metadata()

        LOGGER.info("Start signal received; continuing.")

        if self._metadata.game_timeout is not None:
            LOGGER.info(f"Game length set to {self._metadata.game_timeout}s")
            kill_after_delay(self._metadata.game_timeout)
