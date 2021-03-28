"""Integration with Astoria."""

import asyncio
import logging
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Match, NamedTuple, Optional

from astoria.common.consumer import StateConsumer
from astoria.common.messages.astmetad import Metadata, MetadataManagerMessage
from astoria.common.messages.astprocd import ProcessManagerMessage

LOGGER = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


class GetMetadataResult(NamedTuple):
    """Result returned from fetching metadata from astoria."""

    metadata: Metadata
    usb_path: Path


class GetMetadataConsumer(StateConsumer):
    """Astoria consumer to fetch metadata."""

    name_prefix = "sr-robot3-metadata"

    def _setup_logging(self, verbose: bool, *, welcome_message: bool = True) -> None:
        """Use the logging from sr-robot3."""
        # Suppress INFO messages from gmqtt
        logging.getLogger("gmqtt").setLevel(logging.WARNING)

    def _init(self) -> None:
        """Initialise consumer."""
        self._metadata_message: Optional[MetadataManagerMessage] = None
        self._proc_message: Optional[ProcessManagerMessage] = None
        self._state_lock = asyncio.Lock()
        self._mqtt.subscribe("astmetad", self._handle_astmetad_message)
        self._mqtt.subscribe("astprocd", self._handle_astprocd_message)

    async def _handle_astmetad_message(
        self,
        match: Match[str],
        payload: str,
    ) -> None:
        """Handle astmetad status messages."""
        async with self._state_lock:
            try:
                message = MetadataManagerMessage(**loads(payload))
                if message.status == MetadataManagerMessage.Status.RUNNING:
                    LOGGER.debug("Received metadata")
                    self._metadata_message = message
                else:
                    LOGGER.warn("Cannot get metadata, astmetad is not running")
            except JSONDecodeError:
                LOGGER.error("Could not decode JSON metadata.")
            if self._metadata_message is not None and self._proc_message is not None:
                self.halt(silent=True)

    async def _handle_astprocd_message(
        self,
        match: Match[str],
        payload: str,
    ) -> None:
        """Handle astprocd status messages."""
        async with self._state_lock:
            try:
                message = ProcessManagerMessage(**loads(payload))
                if message.status == ProcessManagerMessage.Status.RUNNING:
                    LOGGER.debug("Received process info")
                    self._proc_message = message
                else:
                    LOGGER.warn("Cannot get process info, astprocd is not running")
            except JSONDecodeError:
                LOGGER.error("Could not decode JSON metadata.")
            if self._metadata_message is not None and self._proc_message is not None:
                self.halt(silent=True)

    async def main(self) -> None:
        """Main method of the command."""
        await self.wait_loop()

    @classmethod
    def get_metadata(cls) -> GetMetadataResult:
        """Get metadata."""
        gmc = cls(False, None)

        metadata = Metadata.init(gmc.config)
        path = Path("/dev/null")

        try:
            loop.run_until_complete(asyncio.wait_for(gmc.run(), timeout=0.1))
            if gmc._metadata_message is not None:
                metadata = gmc._metadata_message.metadata

            if gmc._proc_message is not None and gmc._proc_message.disk_info is not None:
                path = gmc._proc_message.disk_info.mount_path
        except ConnectionRefusedError:
            LOGGER.warning("Unable to connect to MQTT broker")
        except asyncio.exceptions.TimeoutError:
            LOGGER.warning("Astoria took too long to respond, giving up.")

        return GetMetadataResult(metadata, path)
