"""Test that the sr.robot3 imports as expected."""
from enum import Enum
from typing import Callable, Type

import sr.robot3
from j5.boards.sr.v4 import PowerOutputPosition
from j5.components.gpio_pin import GPIOPinMode
from j5.components.motor import MotorSpecialState
from packaging.version import Version
from sr.robot3.types import RobotMode


def test_module_version() -> None:
    """Test that the module has a valid version."""
    assert sr.robot3.__version__ is not None

    version = Version(sr.robot3.__version__)
    assert str(version) == sr.robot3.__version__


def test_enum_constants_are_exported() -> None:
    """Test that constants that are enums are exported at the top level."""
    def check_enum_members_are_exported(
            enum: Type[Enum],
            transform: Callable[[str], str] = lambda x: x,
    ) -> None:
        """Check that all members of an enum are exported at the top level."""
        for member in enum:
            member_from_module = getattr(sr.robot3, transform(member.name))
            assert member is member_from_module

    check_enum_members_are_exported(
        GPIOPinMode,
        lambda x: x[len("DIGITAL_"):] if x.startswith("DIGITAL_") else x,
    )
    check_enum_members_are_exported(MotorSpecialState)
    check_enum_members_are_exported(PowerOutputPosition, lambda x: f"OUT_{x}")
    check_enum_members_are_exported(RobotMode)
