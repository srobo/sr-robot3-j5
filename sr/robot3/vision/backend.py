"""
SR custom behaviour for Zoloto.

- Overriding the camera so that only the markers we want are captured
- Map the development and competition markers into the correct ranges
- Determine the size of a marker given the ID
- Determine which OpenCV calibration to use for the currently connected camera.
"""
import importlib.resources
import logging
from pathlib import Path
from typing import List

from j5_zoloto import ZolotoSingleHardwareBackend
from zoloto.cameras import Camera
from zoloto.marker_type import MarkerType

from sr.robot3.game import get_marker_size

from .strategy import (
    CalibrationStrategy,
    MacSystemStrategy,
    StaticStrategy,
    USBDevicePresentStrategy,
)

LOGGER = logging.getLogger(__name__)

STRATEGIES: List[CalibrationStrategy] = [
    USBDevicePresentStrategy(0x046d, 0x0825, "Logitech C270"),
    USBDevicePresentStrategy(0x046d, 0x0807, "Logitech B500"),
    USBDevicePresentStrategy(0x046d, 0x080a, "Logitech C905"),
    USBDevicePresentStrategy(0x046d, 0x082d, "Logitech C920"),
    USBDevicePresentStrategy(0x0c45, 0x6713, "Microdia Integrated_Webcam_HD"),
    MacSystemStrategy(),
    StaticStrategy("default"),  # Fallback onto something, rather than failing
]


class SRZolotoCamera(Camera):
    """A Zoloto camera that correctly captures markers for SR."""

    def get_marker_size(self, marker_id: int) -> int:
        """
        Get the size of a marker given it's ID.

        :param marker_id: The offical ID number of the marker.
        :returns: The size of the marker in millimetres.
        """
        return get_marker_size(marker_id)


class SRZolotoSingleHardwareBackend(ZolotoSingleHardwareBackend):
    """A camera backend which automatically finds camera calibration data."""

    camera_class = SRZolotoCamera
    marker_type = MarkerType.APRILTAG_36H11

    def get_calibration_file(self) -> Path:
        """Get the calibration file to use."""
        for strategy in STRATEGIES:
            filename = strategy.get_calibration_name()
            if filename is not None:
                LOGGER.info(f"Using {filename} for webcam calibration")
                with importlib.resources.path(
                        "sr.robot3.vision.calibrations",
                        f"{filename}.xml") as path:
                    return path

        # Should not be reachable as the static strategy will always match
        raise RuntimeError("Unable to determine calibration strategy.")
