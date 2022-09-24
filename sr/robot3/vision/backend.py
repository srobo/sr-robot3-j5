"""
SR custom behaviour for Zoloto.

- Overriding the camera so that only the markers we want are captured
- Map the development and competition markers into the correct ranges
- Determine the size of a marker given the ID
- Determine which OpenCV calibration to use for the currently connected camera.
"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from j5_zoloto import ZolotoHardwareBackend
from numpy.typing import NDArray
from zoloto.calibration import parse_calibration_file
from zoloto.cameras import Camera
from zoloto.marker_type import MarkerType

from sr.robot3.game import get_marker_size, marker_used_in_game

from .strategy import (
    CalibrationStrategy,
    MacSystemStrategy,
    USBDevicePresentStrategy,
)

LOGGER = logging.getLogger(__name__)

STRATEGIES: List[CalibrationStrategy] = [
    USBDevicePresentStrategy(0x046d, 0x0825, "Logitech C270"),
    USBDevicePresentStrategy(0x046d, 0x0807, "Logitech B500"),
    USBDevicePresentStrategy(0x046d, 0x080a, "Logitech C905"),
    USBDevicePresentStrategy(0x046d, 0x082d, "Logitech C920"),
    USBDevicePresentStrategy(0x046d, 0x0892, "Logitech C920"),
    USBDevicePresentStrategy(0x046d, 0x08E5, "Logitech C920"),  # C920 PRO
    USBDevicePresentStrategy(0x0c45, 0x6713, "Microdia Integrated_Webcam_HD"),
    MacSystemStrategy(),
]


class SRZolotoCamera(Camera):
    """A Zoloto camera that correctly captures markers for SR."""

    def __init__(
        self,
        camera_id: int,
        *,
        marker_size: Optional[int] = None,
        marker_type: MarkerType,
        calibration_file: Optional[Path] = None,
        marker_offset: int = 0,
    ) -> None:
        resolution: Optional[Tuple[int, int]] = None

        if calibration_file is not None:
            resolution = parse_calibration_file(calibration_file).resolution

        super().__init__(
            camera_id,
            marker_size=marker_size,
            marker_type=marker_type,
            calibration_file=calibration_file,
            resolution=resolution,
        )
        self._marker_offset = marker_offset

    def _get_ids_and_corners(
        self, frame: Optional[NDArray] = None,  # type: ignore[type-arg]
    ) -> Tuple[List[int], List[NDArray]]:  # type: ignore[type-arg]
        raw_ids, raw_corners = super()._get_ids_and_corners(frame)

        ids: List[int] = []
        corners: List[NDArray] = []   # type: ignore[type-arg]

        # Copy list, map marker IDs and filter out ones not in game
        for raw_id, raw_corner in zip(raw_ids, raw_corners):
            offset_id = raw_id - self._marker_offset
            if marker_used_in_game(offset_id):
                ids.append(offset_id)
                corners.append(raw_corner)

        return ids, corners

    def get_marker_size(self, marker_id: int) -> int:
        """
        Get the size of a marker given it's ID.

        :param marker_id: The offical ID number of the marker.
        :returns: The size of the marker in millimetres.
        """
        return get_marker_size(marker_id)


class SRZolotoHardwareBackend(ZolotoHardwareBackend):
    """A camera backend which automatically finds camera calibration data."""

    camera_class = SRZolotoCamera
    marker_type = MarkerType.APRILTAG_36H11

    def __init__(self, camera_id: int, *, marker_offset: int = 0) -> None:
        self._zcam = self.camera_class(
            camera_id,
            marker_type=self.marker_type,
            calibration_file=self.get_calibration_file(),
            marker_size=self.marker_size,
            marker_offset=marker_offset,
        )

    def get_calibration_file(self) -> Optional[Path]:
        """Get the calibration file to use."""
        for strategy in STRATEGIES:
            filename = strategy.get_calibration_name()
            if filename is not None:
                LOGGER.debug(f"Using {filename} for webcam calibration")
                return Path(__file__).parent / f'calibrations/{filename}.xml'

        LOGGER.warning(
            "Unable to determine camera calibration, disabling pose estimation",
        )
        return None
