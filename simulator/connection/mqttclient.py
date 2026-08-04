import json
import threading
import time

import paho.mqtt.client as mqtt

class MQTTClient:

    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="simulator"
        )

        self.connected = False
        self.running = False


    def connect(self):

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

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
            return

        self.client.publish(
            topic,
            json.dumps(payload),
            qos=0,
            retain=False
        )

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self.connected = True

        print(f"[MQTT] Conectado ({reason_code})")


    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.connected = False

        print("[MQTT] Desconectado")