"""Test that the sr.robot3 imports as expected."""

import sr.robot3
from j5.boards.sr.v4 import PowerOutputPosition
from packaging.version import Version


def test_module_version() -> None:
    """Test that the module has a valid version."""
    assert sr.robot3.__version__ is not None

    version = Version(sr.robot3.__version__)
    assert str(version) == sr.robot3.__version__


def test_power_outputs_exported() -> None:
    """Test that the power output constants are exported."""
    EXPORT_PREFIX = "OUT_"

    for pos in PowerOutputPosition:
        pos_from_module = getattr(sr.robot3, EXPORT_PREFIX + pos.name)
        assert pos_from_module is pos
