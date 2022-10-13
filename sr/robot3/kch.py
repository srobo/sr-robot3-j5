"""KCH Daemon Backend."""
import asyncio
import logging
from functools import cached_property
from json import JSONDecodeError, loads
from typing import Match, Optional, Set, Tuple, cast
from uuid import uuid4

from astoria.common.components import StateConsumer
from astoria.common.ipc import ManagerRequest
from j5.backends import Backend
from j5.boards import Board
from j5.boards.sr import KCHBoard
from j5.components import RGBColour, RGBLEDInterface

LOGGER = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


class KCHDaemonConsumer(StateConsumer):
    """KCH Daemon Consumer - Fetch the KCH info."""

    def _setup_logging(self, verbose: bool, *, welcome_message: bool = True) -> None:
        """Use the logging from sr-robot3."""
        # Suppress INFO messages from gmqtt
        logging.getLogger("gmqtt").setLevel(logging.WARNING)

    def _init(self) -> None:
        """Initialise consumer."""
        self._kch_info = None
        self._state_lock = asyncio.Lock()
        self._mqtt.subscribe("kchd", self._handle_kchd_message)

    @cached_property
    def name(self) -> str:
        """
        MQTT client name of the data component.

        This should be unique, as clashes will cause unexpected disconnections.
        """
        return f"sr-robot3-kchd-{uuid4()}"

    async def _handle_kchd_message(
        self,
        match: Match[str],
        payload: str,
    ) -> None:
        """Handle kchd status messages."""
        async with self._state_lock:
            try:
                message = loads(payload)
                if message["status"] == "RUNNING":
                    LOGGER.debug("Received KCH info")
                    self._kch_info = message["kch"]["asset_code"]
                else:
                    LOGGER.warn("kchd is not running")
            except JSONDecodeError:
                LOGGER.error("Could not decode JSON metadata.")
            if message is not None:
                self.halt(silent=True)

    async def main(self) -> None:
        """Main method of the command."""
        await self.wait_loop()

    @classmethod
    def get_kch(cls) -> Optional[str]:
        """Get metadata."""
        kchdc = cls(False, None)

        try:
            loop.run_until_complete(asyncio.wait_for(kchdc.run(), timeout=0.1))
            if kchdc._kch_info is not None:
                return kchdc._kch_info
            else:
                return None
        except ConnectionRefusedError:
            LOGGER.warning("Unable to connect to MQTT broker")
            return None
        except asyncio.TimeoutError:
            LOGGER.warning("KCH Daemon took too long to respond, giving up.")
            return None


class KCHDaemonControlConsumer(StateConsumer):
    """KCH LED Control Consumer."""

    dependencies = ["kchd"]

    def _init(self) -> None:
        self._ready = asyncio.Event()

    def _setup_logging(self, verbose: bool, *, welcome_message: bool = True) -> None:
        """Use the logging from sr-robot3."""
        # Suppress INFO messages from gmqtt
        logging.getLogger("gmqtt").setLevel(logging.WARNING)

    @property
    def name(self) -> str:
        """
        MQTT client name of the data component.

        This should be unique, as clashes will cause unexpected disconnections.
        """
        return f"sr-robot3-kchd-{uuid4()}"

    async def main(self) -> None:
        """Main method of the command."""
        self._ready.set()
        await self.wait_loop()


class KCHLEDUpdateManagerRequest(ManagerRequest):
    """A request to change the controllable LEDs."""

    start: bool = False
    a: Tuple[bool, bool, bool] = (False, False, False)
    b: Tuple[bool, bool, bool] = (False, False, False)
    c: Tuple[bool, bool, bool] = (False, False, False)


class SRKCHDaemonBackend(RGBLEDInterface, Backend):
    """KCH Daemon Backend."""

    board = KCHBoard

    @classmethod
    def discover(cls) -> Set[Board]:
        """
        Discover boards that this backend can control.

        :returns: set of boards that this backend can control.
        """
        info = KCHDaemonConsumer.get_kch()
        if info:
            board = KCHBoard(info, cls())
            return {cast(Board, board)}
        else:
            return set()

    def __init__(self) -> None:
        self._start = False
        self._leds = {
            i: [False, False, False]
            for i in range(3)
        }

        self._kchdc = KCHDaemonControlConsumer(False, None)
        try:
            asyncio.ensure_future(self._kchdc.run())
        except ConnectionRefusedError:
            LOGGER.warning("Unable to connect to MQTT broker")
        except asyncio.TimeoutError:
            LOGGER.warning("KCH Daemon took too long to respond, giving up.")

    async def _set_leds(self) -> None:
        try:
            await asyncio.wait_for(self._kchdc._ready.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            LOGGER.error("Failed to set LED on KCH")
            return
        if not self._kchdc._mqtt.is_connected:
            try:
                # Suppress logging while we reconnect
                logging.disable(logging.ERROR)
                await self._kchdc._mqtt.connect()
            finally:
                logging.disable(logging.NOTSET)
        await self._kchdc._mqtt.manager_request(
            "kchd",
            "user_leds",
            KCHLEDUpdateManagerRequest(
                sender_name=self._kchdc.name,
                start=self._start,
                a=self._leds[0],
                b=self._leds[1],
                c=self._leds[2],
            ),
        )

    def _channel_to_index(self, channel: RGBColour) -> int:
        return {
            RGBColour.RED: 0,
            RGBColour.GREEN: 1,
            RGBColour.BLUE: 2,
        }[channel]

    def _update_leds(self) -> None:
        """Update the LEDs."""
        loop.run_until_complete(self._set_leds())

    def get_rgb_led_channel_duty_cycle(
        self,
        identifier: int,
        channel: RGBColour,
    ) -> float:
        """
        Get the duty cycle of a channel on the LED.

        :param identifier: identifier of the RGB LED.
        :param channel: channel to get the duty cycle for.
        :returns: current duty cycle of the LED.
        """
        return 1.0 if self._leds[identifier][self._channel_to_index(channel)] else 0

    def set_rgb_led_channel_duty_cycle(
        self,
        identifier: int,
        channel: RGBColour,
        duty_cycle: float,
    ) -> None:
        """
        Set the duty cycle of a channel on the LED.

        :param identifier: identifier of the RGB LED.
        :param channel: channel to set the duty cycle of.
        :param duty_cycle: desired duty cycle of the LED.
        """
        self._leds[identifier][self._channel_to_index(channel)] = bool(duty_cycle)
        self._update_leds()
