"""Wrapper around paho-mqtt."""

import atexit
import logging
from typing import Any, Callable, Dict, Optional, Union

import paho.mqtt.client as mqtt
from astoria.common.config import AstoriaConfig

LOGGER = logging.getLogger(__name__)


def init_mqtt(client_name: str = 'sr-robot3') -> 'MQTTClient':
    """
    Helper method to create an MQTT client and connect.

    Uses values from astoria's config.
    """
    config = AstoriaConfig.load()
    client = MQTTClient.establish(
        host=config.mqtt.host,
        port=config.mqtt.port,
        client_name=client_name,
        mqtt_version=(
            mqtt.MQTTv311
            if config.mqtt.force_protocol_version_3_1
            else mqtt.MQTTv5),
        topic_prefix=config.mqtt.topic_prefix,
    )
    return client


class MQTTClient:
    """Class to handle MQTT subscriptions and callbacks."""

    def __init__(
        self,
        client_name: Optional[str] = None,
        mqtt_version: int = mqtt.MQTTv5,
        topic_prefix: Optional[str] = None,
    ) -> None:
        self.subscriptions: Dict[
            str, Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None],
        ] = {}
        self.topic_prefix = topic_prefix
        self._client_name = client_name

        self._client = mqtt.Client(client_id=client_name, protocol=mqtt_version)
        self._client.on_connect = self._on_connect

    def connect(self, host: str, port: int) -> None:
        """
        Connect to the MQTT broker and start event loop in background thread.

        Registers an atexit routine that tears down the client.
        """
        if self._client.is_connected():
            LOGGER.error("Attempting connection, but client is already connected.")
            return

        try:
            self._client.connect(host, port, keepalive=60)
        except (TimeoutError, ValueError, ConnectionRefusedError):
            LOGGER.error(f"Failed to connect to MQTT broker at {host}:{port}")
            return
        self._client.loop_start()
        atexit.register(self.disconnect)

    @classmethod
    def establish(
        cls, host: str, port: int, **kwargs: Any,
    ) -> 'MQTTClient':
        """Create client and connect."""
        client = cls(**kwargs)
        client.connect(host, port)
        return client

    def disconnect(self) -> None:
        """Disconnect from the broker and close background event loop."""
        self._client.disconnect()
        self._client.loop_stop()
        atexit.unregister(self.disconnect)

    def subscribe(
        self,
        topic: str,
        callback: Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None],
        override_prefix: bool = False,
    ) -> None:
        """Subscribe to a topic and assign a callback for messages."""
        if not override_prefix and self.topic_prefix is not None:
            full_topic = f"{self.topic_prefix}/{topic}"
        else:
            full_topic = topic

        self.subscriptions[full_topic] = callback
        self._subscribe(full_topic, callback)

    def _subscribe(
        self,
        topic: str,
        callback: Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None],
    ) -> None:
        LOGGER.debug(f"Subscribing to {topic}")
        self._client.message_callback_add(topic, callback)
        self._client.subscribe(topic, qos=1)

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        try:
            del self.subscriptions[topic]
        except KeyError:
            pass
        self._client.message_callback_remove(topic)
        self._client.unsubscribe(topic)

    def publish(
        self,
        topic: str,
        payload: Union[bytes, str],
        retain: bool = False,
        *,
        auto_prefix_topic: bool = True,
    ) -> None:
        """Publish a message to the broker."""
        if not self._client.is_connected():
            LOGGER.error(
                "Attempted to publish message, but client is not connected.",
            )
            return

        if auto_prefix_topic and self.topic_prefix:
            topic = f"{self.topic_prefix}/{topic}"
        try:
            self._client.publish(topic, payload=payload, retain=retain, qos=1)
        except ValueError:
            raise ValueError(f"Cannot publish to MQTT topic: {topic}")

    def _on_connect(
        self, mqttc: mqtt.Client, obj: Any, flags: Dict[str, int], rc: int,
    ) -> None:
        """Callback run each time the client connects to the broker."""
        for topic, callback in self.subscriptions.items():
            self._subscribe(topic, callback)
