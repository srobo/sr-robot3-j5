"""Integration with Astoria."""

import logging
from json import JSONDecodeError, loads
from pathlib import Path
from queue import PriorityQueue
from threading import Event
from typing import Any, Generic, NamedTuple, Optional, Type, TypeVar

from astoria.common.config import AstoriaConfig
from astoria.common.ipc import (
    BroadcastEvent,
    MetadataManagerMessage,
    ProcessManagerMessage,
    StartButtonBroadcastEvent,
)
from astoria.common.metadata import Metadata
from paho.mqtt.client import Client as MQTT
from paho.mqtt.client import MQTTMessage
from pydantic import ValidationError, parse_obj_as

from .mqtt import MQTTClient

LOGGER = logging.getLogger(__name__)


class GetMetadataResult(NamedTuple):
    """Result returned from fetching metadata from astoria."""

    metadata: Metadata
    usb_path: Path


class GetMetadataConsumer:
    """MQTT consumer to fetch metadata."""

    name = "sr-robot3-metadata"

    def __init__(self, mqtt_client: MQTTClient) -> None:
        self._mqtt = mqtt_client

        # Initialise consumer data structures.
        self._metadata_message: Optional[MetadataManagerMessage] = None
        self._proc_message: Optional[ProcessManagerMessage] = None
        self._astmetad_received = Event()
        self._astprocd_received = Event()

    def run(self, timeout: Optional[float] = None) -> bool:
        """Entrypoint for the data component."""
        self._mqtt.subscribe("astmetad", self._handle_astmetad_message)
        self._mqtt.subscribe("astprocd", self._handle_astprocd_message)

        timeout_step = (timeout / 2) if timeout is not None else None

        # wait for both messages to be received with a timeout
        # the division of time between each step is irrelevant,
        # messages can arrive for either during the whole period
        self._astmetad_received.wait(timeout=timeout_step)
        metadata_received = self._astprocd_received.wait(timeout=timeout_step)

        self._mqtt.unsubscribe("astmetad")
        self._mqtt.unsubscribe("astprocd")

        return metadata_received

    def _handle_astmetad_message(
        self,
        client: MQTT,
        userdata: Any,
        msg: MQTTMessage,
    ) -> None:
        """Handle astmetad status messages."""
        try:
            message = parse_obj_as(MetadataManagerMessage, loads(msg.payload))
            if message.status == MetadataManagerMessage.Status.RUNNING:
                LOGGER.debug("Received metadata")
                self._metadata_message = message
                self._astmetad_received.set()
            else:
                LOGGER.warn("Cannot get metadata, astmetad is not running")
        except JSONDecodeError:
            LOGGER.error("Could not decode JSON metadata.")
        except ValidationError as e:
            LOGGER.error(f"Unable to parse metadata message: {e}")

    def _handle_astprocd_message(
        self,
        client: MQTT,
        userdata: Any,
        msg: MQTTMessage,
    ) -> None:
        """Handle astprocd status messages."""
        try:
            message = parse_obj_as(ProcessManagerMessage, loads(msg.payload))
            if message.status == ProcessManagerMessage.Status.RUNNING:
                LOGGER.debug("Received process info")
                self._proc_message = message
                self._astprocd_received.set()
            else:
                LOGGER.warn("Cannot get process info, astprocd is not running")
        except JSONDecodeError:
            LOGGER.error("Could not decode JSON metadata.")
        except ValidationError as e:
            LOGGER.error(f"Unable to parse process message: {e}")

    @classmethod
    def get_metadata(cls, mqtt_client: MQTTClient) -> GetMetadataResult:
        """Get metadata."""
        gmc = cls(mqtt_client)
        config = AstoriaConfig.load()

        metadata = Metadata.init(config)
        path = Path("/dev/null")

        try:
            metadata_received = gmc.run(timeout=0.1)
            if metadata_received:
                if gmc._metadata_message is not None:
                    metadata = gmc._metadata_message.metadata

                if gmc._proc_message and gmc._proc_message.disk_info:
                    path = gmc._proc_message.disk_info.mount_path
            else:
                LOGGER.warning("Astoria took too long to respond, giving up.")
        except ConnectionRefusedError:
            LOGGER.warning("Unable to connect to MQTT broker")

        return GetMetadataResult(metadata, path)


class WaitForStartButtonBroadcastConsumer:
    """MQTT consumer to wait for a start button broadcast."""

    def __init__(self, mqtt_client: MQTTClient, start_event: Event) -> None:
        self._trigger_event = BroadcastHelper.get_helper(
            mqtt_client,
            StartButtonBroadcastEvent,
            start_event,
        )

        self._start_event = start_event

    def run(self) -> None:
        """Entrypoint for the data component."""
        self._start_event.wait()

    def close(self) -> None:
        """Tidy up BroadcastHelper subscriptions."""
        # run BroadcastHelper __del__ routine to unsubscribe
        del self._trigger_event


T = TypeVar("T", bound=BroadcastEvent)


class BroadcastHelper(Generic[T]):
    """
    Helper class to manage broadcast events.

    Subscribes to broadcast/{name} topic, validates received messages
    against the supplied schema and puts messages in a queue that can
    be read by wait_broadcast.
    """

    def __init__(
        self,
        mqtt: 'MQTTClient',
        name: str,
        schema: Type[T],
        message_event: Optional[Event] = None,
    ) -> None:
        self._mqtt = mqtt
        self._name = name
        self._schema = schema

        self.message_received = message_event if message_event is not None else Event()
        self._event_queue: PriorityQueue[T] = PriorityQueue()
        self._mqtt.subscribe(f"broadcast/{name}", self._handle_broadcast)

    def __del__(self) -> None:
        """Unsubscribe the broadcast topic on destruction."""
        self._mqtt.unsubscribe(f"broadcast/{self._name}")

    @classmethod
    def get_helper(
        cls, mqtt: 'MQTTClient', schema: Type[T], message_event: Optional[Event] = None,
    ) -> 'BroadcastHelper[T]':
        """Get the broadcast helper for a given event."""
        return BroadcastHelper[T](mqtt, schema.name, schema, message_event)

    def _handle_broadcast(
        self,
        client: MQTT,
        userdata: Any,
        msg: MQTTMessage,
    ) -> None:
        """
        Handle a broadcast event message.

        Inserts the event into the priority queue.
        """
        try:
            ev = parse_obj_as(self._schema, loads(msg.payload))
            LOGGER.debug(
                f"Received {ev.event_name} broadcast event from {ev.sender_name}",
            )
            self._event_queue.put(ev)
            self.message_received.set()
        except JSONDecodeError:
            LOGGER.warning(f"Broadcast event {self._name} contained invalid JSON")

    def send(self, **kwargs: Any) -> None:
        """Send an event."""
        data = self._schema(
            event_name=self._schema.name,
            sender_name=self._mqtt._client_name,
            **kwargs,
        )
        self._mqtt.publish(
            f"broadcast/{self._schema.name}",
            data.json(),
        )

    def wait_broadcast(self, timeout: Optional[float] = None) -> T:
        """Wait for an event on the given broadcast."""
        return self._event_queue.get(timeout=timeout)
