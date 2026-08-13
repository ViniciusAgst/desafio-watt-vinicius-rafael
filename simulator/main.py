import logging
import threading
import time

from assets.devices.aircompressor import AirCompressor
from assets.devices.extruder import Extruder
from assets.devices.grid import Grid
from connection.mqttclient import MQTTClient
from dashboard import Dashboard
from common.logger import info, error


def main():
    logging.getLogger("werkzeug").disabled = True

    info("MAIN", "Iniciando simulador")

    mqtt = MQTTClient()

    info("MQTT", "Conectando ao broker...")

    mqtt.connect()

    info("MQTT", "Conectado")

    grid = Grid("Rede Elétrica")
    compressor = AirCompressor("Compressor")
    extruder = Extruder("Extrusora")

    dashboard = Dashboard(grid, compressor, extruder)

    grid.start()
    compressor.start()
    extruder.start()

    info("DEVICE", "Dispositivos inicializados")

    threading.Thread(
        target=dashboard.start,
        daemon=True
    ).start()

    time.sleep(2)

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
    try:
        main()
    except KeyboardInterrupt:
        info("MAIN", "Simulador encerrado")
    except Exception as e:
        error("MAIN", f"Erro inesperado: {e}")