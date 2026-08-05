import threading
import time

from assets.devices.aircompressor import AirCompressor
from assets.devices.extruder import Extruder
from assets.devices.grid import Grid
from connection.mqttclient import MQTTClient
from dashboard import Dashboard


def main():
    mqtt = MQTTClient()

    print("Conectando ao broker...")

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
            "simulador/grid",
            grid.get_data()
        )

        mqtt.publish(
            "simulador/aircompressor",
            compressor.get_data()
        )

        mqtt.publish(
            "simulador/extruder",
            extruder.get_data()
        )

        time.sleep(1)

if __name__ == "__main__":
    main()