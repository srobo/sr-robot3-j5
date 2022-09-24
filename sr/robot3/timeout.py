"""Code to kill robot after certain amount of time."""
import logging
from signal import SIGALRM, alarm, signal
from types import FrameType
from typing import Optional

LOGGER = logging.getLogger(__name__)


def timeout_handler(signal_type: int, stack_frame: Optional[FrameType]) -> None:
    """Handle the `SIGALRM` to kill the current process."""
    raise SystemExit("Timeout expired: Game Over!")


def kill_after_delay(timeout_seconds: int) -> None:
    """Interrupts main process after the given delay."""
    LOGGER.debug(f"Kill Signal Timeout set: {timeout_seconds}s")
    signal(SIGALRM, timeout_handler)
    alarm(timeout_seconds)
