"""Strategies for determining the camera on given hardware."""
import json
import platform
import subprocess
from abc import ABCMeta, abstractmethod
from typing import Optional

import usb


class CalibrationStrategy(metaclass=ABCMeta):
    """Base calibration strategy used to determine the correct camera calibration file."""

    @abstractmethod
    def get_calibration_name(self) -> Optional[str]:
        """Get the name of the calibration profile."""
        raise NotImplementedError


class StaticStrategy(CalibrationStrategy):
    """A strategy that always returns the same calibration profile."""

    def __init__(self, calibration_name: str) -> None:
        self._calibration_name = calibration_name

    def get_calibration_name(self) -> Optional[str]:
        """Get the name of the calibration profile."""
        return self._calibration_name


class USBDevicePresentStrategy(CalibrationStrategy):
    """Strategy used for determining calibration profile based on present USB devices."""

    def __init__(
            self,
            vendor_id: int,
            product_id: int,
            calibration_name: str,
    ) -> None:
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._calibration_name = calibration_name

    def get_calibration_name(self) -> Optional[str]:
        """Gets the name of the calibration profile."""
        if usb.core.find(
                idVendor=self._vendor_id,
                idProduct=self._product_id,
        ) is not None:
            return self._calibration_name
        else:
            return None


class MacSystemStrategy(CalibrationStrategy):
    """Strategy used for determining calibration profile on macOS."""

    def get_calibration_name(self) -> Optional[str]:
        """Get the name of the calibration profile."""
        if platform.system() == "Darwin":  # macOS
            return self._find_default_camera()
        return None

    def _find_default_camera(self) -> Optional[str]:
        camera_info = json.loads(
            subprocess.check_output(['system_profiler', '-json', 'SPCameraDataType']),
        )
        first_camera = camera_info['SPCameraDataType'][0]
        if first_camera['_name'] == 'FaceTime HD Camera':
            return 'FaceTime HD Camera'
        return None
