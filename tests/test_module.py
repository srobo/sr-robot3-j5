"""Test that the sr.robot3 imports as expected."""
from enum import Enum
from typing import Type

import sr.robot3
from j5.boards.sr.v4 import PowerOutputPosition
from j5.components.motor import MotorSpecialState
from packaging.version import Version


def test_module_version() -> None:
    """Test that the module has a valid version."""
    assert sr.robot3.__version__ is not None

    version = Version(sr.robot3.__version__)
    assert str(version) == sr.robot3.__version__


def test_enum_constants_are_exported() -> None:
    """Test that constants that are enums are exported at the top level."""
    def check_enum_members_are_exported(enum: Type[Enum], prefix: str = "") -> None:
        """Check that all members of an enum are exported at the top level."""
        for member in enum:
            member_from_module = getattr(sr.robot3, prefix + member.name)
            assert member is member_from_module

    check_enum_members_are_exported(MotorSpecialState)
    check_enum_members_are_exported(PowerOutputPosition, "OUT_")
