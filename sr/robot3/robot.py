"""sr.robot3 Robot class."""

import logging
import os
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from april_vision.j5 import AprilCameraBoard
from astoria.common.metadata import Metadata, RobotMode
from j5 import BaseRobot, Environment
from j5 import __version__ as j5_version
from j5.backends import Backend
from j5.boards import Board, BoardGroup
from j5.boards.sr.v4 import MotorBoard, PowerBoard, Ruggeduino, ServoBoard
from j5.components.piezo import Note
from serial.tools.list_ports_common import ListPortInfo

from .astoria import GetMetadataConsumer, WaitForStartButtonBroadcastConsumer
from .env import HARDWARE_ENVIRONMENT
from .game import MARKER_SIZES
from .kch import KCH
from .mqtt import init_mqtt
from .timeout import kill_after_delay

__version__ = "2023.2.0"


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
            auto_start: bool = False,
            verbose: bool = False,
            env: Environment = HARDWARE_ENVIRONMENT,
            ignored_ruggeduinos: Optional[List[str]] = None,
            legacy_camera_axis: bool = True,
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
        :param legacy_camera_axis: Use the coordinate systems the camera used
            prior to SR OS 2023.1.0.
        """
        self._auto_start = auto_start
        self._verbose = verbose
        self._environment = env

        if verbose:
            # Set root logger to DEBUG level
            logging.getLogger().setLevel(logging.DEBUG)
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

        self._mqtt = init_mqtt()

        self._init_metadata()

        self._init_cameras(self.metadata.marker_offset)
        if legacy_camera_axis:
            LOGGER.info("Using legacy coordinate system for vision")
            os.environ['ZOLOTO_LEGACY_AXIS'] = '1'
        else:
            LOGGER.info("Using updated coordinate system for vision")
        self._init_power_board()
        self._init_auxiliary_boards()

        self._init_ruggeduinos()

        self._log_discovered_boards()

        if auto_start:
            LOGGER.debug("Auto start is enabled.")
        else:
            LOGGER.debug("Auto start is disabled.")
            self.wait_start()

    def _init_cameras(self, marker_offset: int) -> None:
        """Initialise vision system for a single camera."""
        def mqtt_publish_callback(topic: str, payload: Union[bytes, str]) -> None:
            self._mqtt.publish(topic, payload, auto_prefix_topic=False)

        self._cameras: BoardGroup[AprilCameraBoard, Backend]
        try:
            # Setup calibration file locations
            from .vision.calibrations import __file__ as calibrations

            # get any pre-defined calibration locations
            current_calibrations = os.environ.get('OPENCV_CALIBRATIONS', '')
            calibration_locs = ':'.join(
                [current_calibrations, os.path.dirname(calibrations)])
            os.environ['OPENCV_CALIBRATIONS'] = calibration_locs.strip(':')

            self._cameras = self._environment.get_board_group(AprilCameraBoard)
            # setup marker sizes
            for cam in self._cameras:
                cam._backend.set_marker_sizes(
                    MARKER_SIZES, marker_offset=marker_offset)

                # Insert a reference to the MQTT client into the camera backend
                # to allow frames to be sent to the website
                cam._backend._mqtt_publish = mqtt_publish_callback
        except NotImplementedError:
            LOGGER.warning("No camera backend found")

    def _init_power_board(self) -> None:
        """
        Find and initialise the power board.

        The power board is is the only required board.
        """
        self._power_boards = self._environment.get_board_group(PowerBoard)
        self._power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _init_auxiliary_boards(self) -> None:
        """Find and initialise auxiliary boards."""
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
        self._metadata, self._code_path = GetMetadataConsumer.get_metadata(
            self._mqtt,
        )
        offset = self._metadata.marker_offset
        if hasattr(self, '_cameras'):
            for camera in self._cameras:
                try:
                    # Update enabled markers
                    camera._backend.set_marker_sizes(
                        MARKER_SIZES, marker_offset=offset)
                except AttributeError:
                    pass

    def _log_discovered_boards(self) -> None:
        """Log all boards that we have discovered."""
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name} - {board.serial_number}")
            LOGGER.debug(
                f"Firmware Version of {board.serial_number}: {board.firmware_version}",
            )

    @property
    def camera(self) -> AprilCameraBoard:
        """
        Get the robot's camera interface.

        :returns: a :class:`april_vision.j5.AprilCameraBoard`.
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

    @property
    def is_simulated(self) -> bool:
        """
        Determine whether the robot is simulated.

        :returns: True if the robot is simulated. False otherwise.
        """
        return False

    def print_wifi_details(self) -> None:
        """Prints the current WiFi details stored in robot-settings.toml."""
        if not self.metadata.wifi_enabled:
            LOGGER.warn("Could not print WiFi details - WiFi is not enabled")
            return
        LOGGER.info("WiFi credentials:")
        LOGGER.info(f"SSID: {self.metadata.wifi_ssid}")
        LOGGER.info(f"Password: {self.metadata.wifi_psk}")

    def sleep(self, secs: float) -> None:
        """
        Wait for the specified amount of time.

        This exists for compatibility with the simulator API only.

        :param secs: the number of seconds to wait for.
        """
        return time.sleep(secs)

    def time(self) -> float:
        """
        Get the number of seconds since the Unix Epoch.

        This exists for compatibility with the simulator API only.

        :returns: the number of seconds since the Unix Epoch.
        """
        return time.time()

    def wait_start(self) -> None:
        """
        Wait for a start signal.

        Intended for use with `Robot(auto_start=False)`, to allow
        students to run code and setup their robot before the start
        of a match.
        """
        LOGGER.info("Waiting for start signal")

        start_event = threading.Event()

        astoria_start = WaitForStartButtonBroadcastConsumer(
            self._mqtt,
            start_event,
        )

        self.power_board.piezo.buzz(timedelta(seconds=0.1), Note.A6)
        counter = 0
        led_state = False
        _ = self.power_board.start_button.is_pressed
        while not self.power_board.start_button.is_pressed and \
                not start_event.is_set():
            if counter % 6 == 0:
                led_state = not led_state
                self.power_board._run_led.state = led_state
                self.kch.start = led_state
            time.sleep(0.05)
            counter += 1

        # Tidy up wait start subscriptions
        astoria_start.close()

        # Turn on the LED now that we are starting
        self.power_board._run_led.state = True

        # Turn off the KCH Start LED.
        self.kch.start = False

        # Reload metadata as a metadata USB may have been inserted.
        # This ensures that the game timeout is observed even if the metadata
        # USB is inserted after usercode execution begins.
        self._init_metadata()

        LOGGER.info("Start signal received; continuing.")

        if self._metadata.game_timeout is not None:
            LOGGER.info(f"Game length set to {self._metadata.game_timeout}s")
            kill_after_delay(self._metadata.game_timeout)
