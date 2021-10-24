from typing import List

import sr.robot3

project = "Student Robotics API"
copyright = "2021, Student Robotics"  # noqa: A001
author = "Student Robotics Kit Team"

release = sr.robot3.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.graphviz',
    "sphinx_rtd_theme",
]

templates_path = []  # type: List[str]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "astoria": ("https://srobo.github.io/astoria/", None),
    "j5": ("https://j5.org.uk/en/main/", None),
    "j5_zoloto": ("https://j5api.github.io/j5-zoloto/", None),
    "python": ("https://docs.python.org/3", None),
}

html_theme = "sphinx_rtd_theme"

html_static_path = []  # type: List[str]

autodoc_default_options = {
    "member-order": "alphabetical",
    "special-members": "__init__",
    "undoc-members": True,
    # "inherited-members": True,
}

autodoc_mock_imports = []

source_suffix = [".rst", ".md"]