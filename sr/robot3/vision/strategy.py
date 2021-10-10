"""Strategies for determining the camera on given hardware."""
import json
import subprocess
from abc import ABCMeta
import platform
from typing import Optional
import usb

class CalibrationStrategy(metaclass=ABCMeta):

    def get_calibration_name(self) -> Optional[str]:
        raise NotImplementedError


class StaticStrategy(CalibrationStrategy):

    def __init__(self, calibration_name: str) -> None:
        self._calibration_name = calibration_name

    def get_calibration_name(self) -> Optional[str]:
        return self._calibration_name


class USBDevicePresentStrategy(CalibrationStrategy):

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

        if usb.core.find(idVendor=self._vendor_id, idProduct=self._product_id) is not None:
            return self._calibration_name
        else:
            return None


class MacSystemStrategy(CalibrationStrategy):

    def get_calibration_name(self) -> Optional[str]:
        if platform.system() == "Darwin":
            return self._find_default_camera()
        return None

    def _find_default_camera(self) -> Optional[str]:
        camera_info = json.loads(subprocess.check_output(['system_profiler', '-json', 'SPCameraDataType']))
        first_camera = camera_info['SPCameraDataType'][0]
        if first_camera['_name'] == 'FaceTime HD Camera':
            return 'FaceTime HD Camera'
        return None


