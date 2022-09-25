"""Integration with Astoria."""

import asyncio
import logging
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Match, NamedTuple, Optional

from astoria.common.components import StateConsumer
from astoria.common.ipc import (
    MetadataManagerMessage,
    ProcessManagerMessage,
    StartButtonBroadcastEvent,
)
from astoria.common.metadata import Metadata
from astoria.common.mqtt import BroadcastHelper
from pydantic import parse_obj_as

LOGGER = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


class GetMetadataResult(NamedTuple):
    """Result returned from fetching metadata from astoria."""

    metadata: Metadata
    usb_path: Path


class GetMetadataConsumer(StateConsumer):
    """Astoria consumer to fetch metadata."""

    name = "sr-robot3-metadata"

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
                message = parse_obj_as(MetadataManagerMessage, loads(payload))
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
                message = parse_obj_as(ProcessManagerMessage, loads(payload))
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
        except asyncio.TimeoutError:
            LOGGER.warning("Astoria took too long to respond, giving up.")

        return GetMetadataResult(metadata, path)


class WaitForStartButtonBroadcastConsumer(StateConsumer):
    """Wait for a start button broadcast."""

    name = "sr-robot3-wait-start"

    def __init__(
        self,
        verbose: bool,
        config_file: Optional[str],
        start_event: asyncio.Event,
    ) -> None:
        super().__init__(verbose, config_file)
        self._start_event = start_event

    def _setup_logging(self, verbose: bool, *, welcome_message: bool = True) -> None:
        """Use the logging from sr-robot3."""
        # Suppress INFO messages from gmqtt
        logging.getLogger("gmqtt").setLevel(logging.WARNING)

    def _init(self) -> None:
        """
        Initialisation of the data component.

        Called in the constructor of the parent class.
        """
        self._trigger_event = BroadcastHelper.get_helper(
            self._mqtt,
            StartButtonBroadcastEvent,
        )

    async def main(self) -> None:
        """Wait for a trigger event."""
        while not self._start_event.is_set():
            # wait_broadcast waits forever until a broadcoast, so we will use a short
            # timeout to ensure that the loop condition is checked.
            try:
                await asyncio.wait_for(self._trigger_event.wait_broadcast(), timeout=0.1)
                self._start_event.set()
            except asyncio.TimeoutError:
                pass
