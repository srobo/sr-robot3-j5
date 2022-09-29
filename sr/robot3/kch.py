"""KCH Daemon Backend."""
import logging
from typing import Optional, Set, Tuple, cast

from j5.backends import Backend
from j5.boards import Board
from j5.boards.sr import KCHBoard
from j5.components import RGBColour, RGBLEDInterface
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)


class KCHLEDUpdate(BaseModel):
    """A request to change the controllable LEDs."""

    start: bool = False
    a: Tuple[bool, bool, bool] = (False, False, False)
    b: Tuple[bool, bool, bool] = (False, False, False)
    c: Tuple[bool, bool, bool] = (False, False, False)


class KCHHTTPClient:
    """HTTP Client to control kchd via asthttpd."""

    def get_kch(self) -> Optional[str]:
        """Get the asset code of the KCH."""
        return None

    def set_leds(self, state: KCHLEDUpdate) -> None:
        """Set the leds."""
        pass


class SRKCHDaemonBackend(RGBLEDInterface, Backend):
    """KCH Daemon Backend."""

    board = KCHBoard

    @classmethod
    def discover(cls) -> Set[Board]:
        """
        Discover boards that this backend can control.

        :returns: set of boards that this backend can control.
        """
        client = KCHHTTPClient()
        info = client.get_kch()
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

        self._client = KCHHTTPClient()

    def _set_leds(self) -> None:
        self._client.set_leds(
            KCHLEDUpdate(
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
        self._set_leds()
