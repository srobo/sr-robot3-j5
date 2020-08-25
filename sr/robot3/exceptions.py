"""Exceptions."""


class BadFifoException(Exception):
    """The supplied fifo was invalid."""


class MetadataErrorException(Exception):
    """There was an error loading metadata."""
