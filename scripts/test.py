import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend

from sphinx.directives.code import setup as setup_code

from typing import Set
from pathlib import Path

setup_code()

def parse_rst(text: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)
    return document


ignored_flake8_rules: Set[str] = set()

class SnippetWriter:
    """Writes files with sequentially increasing numbers into a directory."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.next_num = 0

    def write(self, contents: str) -> None:
        """
        Write the next file using the given contents.
        :param contents: contents of file.
        """
        contents = f"# noqa: {','.join(ignored_flake8_rules)}\n{contents}"
        path = self.output_path / f"snippet{self.next_num:04d}.py"
        with open(path, "w") as file:
            file.write(contents)
        self.next_num += 1

sw = SnippetWriter(Path("docs/snippets"))

class MyVisitor(docutils.nodes.NodeVisitor):

    def visit_literal_block(self, node: docutils.nodes.Node) -> None:
        sw.write(node.astext())

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        """Called for all other node types."""
        pass

if __name__ == "__main__":

    for file in Path("docs").rglob("*.rst"):
        with file.open() as fh:
            doc = parse_rst(fh.read())
        visitor = MyVisitor(doc)
        doc.walk(visitor)