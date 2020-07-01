"""Test that the sr.robot3 imports as expected."""
import sr.robot3
from packaging.version import Version


def test_module_version() -> None:
    """Test that the module has a valid version."""
    assert sr.robot3.__version__ is not None

    version = Version(sr.robot3.__version__)
    assert str(version) == sr.robot3.__version__
