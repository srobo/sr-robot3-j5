"""KCH Driver."""
from enum import IntEnum, unique
from typing import List, Tuple, Union
from warnings import catch_warnings

try:
    import RPi.GPIO as GPIO  # isort: ignore
    HAS_HAT = True
except ImportError:
    HAS_HAT = False


@unique
class RobotLEDs(IntEnum):
    """Mapping of LEDs to GPIO Pins."""

    START = 9

    USER_A_RED = 24
    USER_A_GREEN = 10
    USER_A_BLUE = 25
    USER_B_RED = 27
    USER_B_GREEN = 23
    USER_B_BLUE = 22
    USER_C_RED = 4
    USER_C_GREEN = 18
    USER_C_BLUE = 17

    @classmethod
    def all_leds(cls) -> List[int]:
        """Get all LEDs."""
        return [c.value for c in cls]

    @classmethod
    def user_leds(cls) -> List[Tuple[int, int, int]]:
        """Get the user programmable LEDs."""
        return [
            (cls.USER_A_RED, cls.USER_A_GREEN, cls.USER_A_BLUE),
            (cls.USER_B_RED, cls.USER_B_GREEN, cls.USER_B_BLUE),
            (cls.USER_C_RED, cls.USER_C_GREEN, cls.USER_C_BLUE),
        ]


@unique
class UserLED(IntEnum):
    """User Programmable LEDs."""

    A = 0
    B = 1
    C = 2


class Colour():
    """User LED colours."""

    OFF = (False, False, False)
    RED = (True, False, False)
    YELLOW = (True, True, False)
    GREEN = (False, True, False)
    CYAN = (False, True, True)
    BLUE = (False, False, True)
    MAGENTA = (True, False, True)
    WHITE = (True, True, True)


class KCH:
    """KCH Board."""

    def __init__(self) -> None:
        if HAS_HAT:
            GPIO.setmode(GPIO.BCM)
            with catch_warnings():
                # If this is not the first time the code is run this init will
                # cause a warning as the gpio are alrady initilized, we can
                # suppress this as we know the reason behind the warning
                GPIO.setup(RobotLEDs.all_leds(), GPIO.OUT, initial=GPIO.LOW)
        self._leds = LEDs(RobotLEDs.user_leds())

    def __del__(self) -> None:
        # We are not running cleanup so the LED state persits after the code completes,
        # this will cause a warning with `GPIO.setup()` which we can suppress
        if HAS_HAT:
            # GPIO.cleanup()
            pass

    @property
    def start(self) -> bool:
        """Get the state of the start LED."""
        return GPIO.input(RobotLEDs.START) if HAS_HAT else False

    @start.setter
    def start(self, value: bool) -> None:
        """Set the state of the start LED."""
        if HAS_HAT:
            GPIO.output(RobotLEDs.START, GPIO.HIGH if value else GPIO.LOW)

    @property
    def leds(self) -> 'LEDs':
        """User programmable LEDs."""
        return self._leds


class LEDs:
    """Programmable LEDs controller."""

    def __init__(self, leds: List[Tuple[int, int, int]]):
        self._leds = leds

    def __setitem__(self, key: Union[int, slice], value: Tuple[bool, bool, bool]) -> None:
        """
        Set the colour of a user LED.

        :param key: The index of the RGB LED to set.
        :param value: A 3-tuple of the subpixel values as bools.
        :returns: None.
        :raises ValueError: value wasn't a tuple with 3 elements.
        :raises IndexError: An index outside range(3) was requested.
        """
        rgb_leds = []
        if isinstance(key, slice):
            rgb_leds = self._leds[key]
        elif isinstance(key, int):
            rgb_leds = [self._leds[key]]

        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("The LED requires 3 values for it's colour")

        if HAS_HAT:
            for rgb_led in rgb_leds:
                for led, state in zip(rgb_led, value):
                    GPIO.output(led, GPIO.HIGH if state else GPIO.LOW)

    def __getitem__(self, key: Union[int, slice]) -> Union['LED', List['LED']]:
        """
        Get the colour of a user LED.

        :param key: The index of the RGB LED to get the colour of.
        :returns: A 3-tuple of the subpixel values as bools.
        :raises IndexError: An index outside range(3) was requested.
        """
        if isinstance(key, slice):
            return [LED(led) for led in self._leds[key]]
        elif isinstance(key, int):
            return LED(self._leds[key])

    def __len__(self) -> int:
        return len(self._leds)


class LED:
    """User programmable LED."""

    def __init__(self, led: Tuple[int, int, int]):
        self._led = led

    @property
    def r(self) -> bool:
        """Get the state of the Red LED segment."""
        return GPIO.input(self._led[0]) if HAS_HAT else False

    @r.setter
    def r(self, value: bool) -> None:
        """Set the state of the Red LED segment."""
        if HAS_HAT:
            GPIO.output(self._led[0], GPIO.HIGH if value else GPIO.LOW)

    @property
    def g(self) -> bool:
        """Get the state of the Green LED segment."""
        return GPIO.input(self._led[1]) if HAS_HAT else False

    @g.setter
    def g(self, value: bool) -> None:
        """Set the state of the Green LED segment."""
        if HAS_HAT:
            GPIO.output(self._led[1], GPIO.HIGH if value else GPIO.LOW)

    @property
    def b(self) -> bool:
        """Get the state of the Blue LED segment."""
        return GPIO.input(self._led[2]) if HAS_HAT else False

    @b.setter
    def b(self, value: bool) -> None:
        """Set the state of the Blue LED segment."""
        if HAS_HAT:
            GPIO.output(self._led[2], GPIO.HIGH if value else GPIO.LOW)
