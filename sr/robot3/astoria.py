"""Integration with Astoria."""

import asyncio
import logging
from json import JSONDecodeError, loads
from typing import Match, Optional

from astoria.common.consumer import StateConsumer
from astoria.common.messages.astmetad import Metadata, MetadataManagerMessage

LOGGER = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


class GetMetadataConsumer(StateConsumer):
    """Astoria consumer to fetch metadata."""

    name_prefix = "sr-robot3-metadata"

    def _setup_logging(self, verbose: bool, *, welcome_message: bool = True) -> None:
        """Use the logging from sr-robot3."""
        # Suppress INFO messages from gmqtt
        logging.getLogger("gmqtt").setLevel(logging.WARNING)

    def _init(self) -> None:
        """Initialise consumer."""
        self._data: Optional[MetadataManagerMessage] = None
        self._mqtt.subscribe("astmetad", self._handle_raw_message)

    async def _handle_raw_message(
        self,
        match: Match[str],
        payload: str,
    ) -> None:
        """Handle astmetad status messages."""
        try:
            message = MetadataManagerMessage(**loads(payload))
            if message.status == MetadataManagerMessage.Status.RUNNING:
                LOGGER.debug("Received metadata")
                self._data = message
            else:
                LOGGER.warn("Cannot get metadata, astmetad is not running")
        except JSONDecodeError:
            LOGGER.error("Could not decode JSON metadata.")
        self.halt(silent=True)

    async def main(self) -> None:
        """Main method of the command."""
        await self.wait_loop()

    @classmethod
    def get_metadata(cls) -> Metadata:
        """Get metadata."""
        gmc = cls(False, None)
        loop.run_until_complete(gmc.run())
        if gmc._data is None:
            return Metadata.init(gmc.config)  # Return default
        else:
            return gmc._data.metadata
