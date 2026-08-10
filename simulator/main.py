import logging
import threading
import time

from assets.devices.aircompressor import AirCompressor
from assets.devices.extruder import Extruder
from assets.devices.grid import Grid
from connection.mqttclient import MQTTClient
from dashboard import Dashboard


def main():
    logging.getLogger("werkzeug").disabled = True

    mqtt = MQTTClient()

    print("[MQTT] Conectando ao broker...")

    mqtt.connect()

    grid = Grid("Rede Elétrica")
    compressor = AirCompressor("Compressor")
    extruder = Extruder("Extrusora")

    dashboard = Dashboard(grid, compressor, extruder)

    grid.start()
    compressor.start()
    extruder.start()

    threading.Thread(
        target=dashboard.start,
        daemon=True
    ).start()

    while True:
        compressor.update()

        extruder.update()

        grid.update([compressor, extruder])

        mqtt.publish(
            "simulator/grid",
            grid.get_data()
        )

        mqtt.publish(
            "simulator/aircompressor",
            compressor.get_data()
        )

        mqtt.publish(
            "simulator/extruder",
            extruder.get_data()
        )

        time.sleep(1)

if __name__ == "__main__":
    main()