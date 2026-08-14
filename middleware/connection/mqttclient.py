import json

import paho.mqtt.client as mqtt

from logger import debug
from middleware.storage.storagemanager import StorageManager

class MQTTClient:

    def __init__(self, storage: StorageManager):

        self.storage = storage

        self.client = mqtt.Client(
            client_id="simulator_client"
        )

        self.connected = False
        self.running = False

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def connect(self):
        self.running = True
        self.client.connect("localhost", 1883)

    def disconnect(self):
        self.running = False
        self.client.disconnect()

    def loop_forever(self):
        self.client.loop_forever()



    def _on_connect(self, client, userdata, flags, rc):
        self.connected = True

        client.subscribe("simulator/grid", qos=0)
        client.subscribe("simulator/extruder", qos=0)
        client.subscribe("simulator/aircompressor", qos=0)



    def _on_disconnect(self, client, userdata, rc):
        self.connected = False



    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print("Payload inválido em %s: %s", msg.topic, exc)
            return

        source = msg.topic.split("/")[-1]

        self.storage.put(source, payload)

        debug(
            "MQTT",
            f"Mensagem processada: fonte={source}, registros={payload}"
        )
