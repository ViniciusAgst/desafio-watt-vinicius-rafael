import json
import threading
import time

import paho.mqtt.client as mqtt

from logger import warn, error, debug


class MQTTClient:

    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="simulator"
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.connected = False
        self.running = False


    def connect(self):
        self.client.connect("localhost", 1883)

        self.running = True

        threading.Thread(
            target=self.client.loop_forever,
            daemon=True
        ).start()

        while not self.connected:
            time.sleep(0.1)


    def disconnect(self):

        self.running = False
        self.client.disconnect()


    def publish(self, topic: str, payload: dict):

        if not self.connected:
            warn("MQTT", f"Publicação ignorada, sem conexão: {topic}")
            return

        try:
            self.client.publish(
                topic,
                json.dumps(payload),
                qos=0,
                retain=False
            )

            debug("MQTT", f"Publicado: {topic} -> {payload}")

        except Exception as e:
            error("MQTT", f"Erro ao publicar em {topic}: {e}")


    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self.connected = True


    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.connected = False

        if self.running:
            warn("MQTT", "Conexão perdida")