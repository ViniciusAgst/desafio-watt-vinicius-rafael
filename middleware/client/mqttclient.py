
import paho.mqtt.client as mqtt


class MQTTClient:

    def __init__(self, callback):

        self.client = mqtt.Client()

        self.client.on_message = callback


    def connect(self):

        self.client.connect(
            "localhost",
            1883
        )


    def subscribe(self):

        self.client.subscribe(
            "simulador/#"
        )


    def loop(self):

        self.client.loop_forever()