# sr.robot3

![Tests](https://github.com/srobo/sr-robot3/workflows/Tests/badge.svg)
[![PyPI version](https://badge.fury.io/py/sr.robot3.svg)](https://pypi.org/project/sr.robot3/)
[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://opensource.org/licenses/MIT)
![Bees](https://img.shields.io/badge/bees-110%25-yellow.svg)

Student Robotics API for Python 3

This package uses [PEP420](https://www.python.org/dev/peps/pep-0420/)-style namespace packaging.

## Development

### Requirements

This project uses the [Poetry](https://python-poetry.org) dependency and virtualenv manager.

You will also need:

- Python 3.8+
- Make

### Setup

- Clone the repository from GitHub to a folder on your local machine
- `cd` to that folder, and tell Poetry to install dependencies and set up a virtualenv `poetry install`
- You can now enter the virtual environment using `poetry shell` and develop using your IDE of choice.

### Tests

The full type, test and lint suite can be run using make: `make`.

You can also run parts of the suite.

- Unit tests: `make test`
- Unit tests with HTML coverage: `make test-cov`
- Linting: `make lint`
- Static type checks: `make type`

### Adding camera calibrations

You will need to print off a [chAruco marker grid](https://docs.opencv.org/4.5.3/charuco_board.png).

`opencv_interactive-calibration -t=charuco -sz=GRID_SIZE`

Replace GRID_SIZE with the length of one of the larger squares (in mm) from the printed marker grid.

Use `-ci=1` for specifying camera index if multiple cameras are connected.

Point the camera at the marker grid. Until DF is at or below 30 then press S to save.
This will output a `cameraParameters.xml` file. Place this file in `sr/robot3/vision/calibrations` named by the camera model.

You will need to add a detection strategy for the camera in to `sr/robot3/vision/backend.py`.

## Contributions

This project is released under the MIT Licence. For more information, please see LICENSE.

The CONTRIBUTORS file can be generated by executing CONTRIBUTORS.gen. This generated file contains a list of people who have contributed to sr.robot3.
