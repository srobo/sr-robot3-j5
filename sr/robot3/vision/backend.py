import importlib.resources
import logging
from pathlib import Path
from typing import List

from j5_zoloto import ZolotoSingleHardwareBackend

from .strategy import CalibrationStrategy, MacSystemStrategy, StaticStrategy, USBDevicePresentStrategy

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


class SRZolotoSingleHardwareBackend(ZolotoSingleHardwareBackend):
    """A camera backend which automatically finds camera calibration data."""

    def get_calibration_file(self) -> Path:
        """Get the calibration file to use."""
        for strategy in STRATEGIES:
            filename = strategy.get_calibration_name()
            if filename is not None:
                LOGGER.info(f"Using {filename} for webcam calibration")
                with importlib.resources.path("sr.robot3.vision.calibrations", f"{filename}.xml") as path:
                    return path

        # Should not be reachable as the static strategy will always match
        raise RuntimeError("Unable to determine calibration strategy.")
