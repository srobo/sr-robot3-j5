"""Game specific code."""
from typing import Container, Dict


class UnusedMarkerException(Exception):
    """This marker is not used for the game."""


MARKER_SIZES: Dict[Container[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 100,  # Everything else is a token
}


def marker_used_in_game(marker_id: int) -> bool:
    """
    Determine whether the marker ID is used in the game.

    :param marker_id: An official marker number, mapped to the competitor range.
    :returns: True if the market is used in the game.
    """
    return any([marker_id in marker_range for marker_range in MARKER_SIZES])


def get_marker_size(marker_id: int) -> int:
    """
    Get the size of a marker in millimetres.

    :param marker_id: An official marker number, mapped to the competitor range.
    :returns: Size of the marker in millimetres.
    """
    for marker_range, size in MARKER_SIZES.items():
        if marker_id in marker_range:
            return size
    raise UnusedMarkerException(f"{marker_id} is not used for the game.")
