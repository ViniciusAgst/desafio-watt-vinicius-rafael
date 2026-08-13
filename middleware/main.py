from time import sleep

from common.logger import info, error

from middleware.connection.mqttclient import MQTTClient
from middleware.opc.server import OpcUaServer
from middleware.storage.buffer import SQLiteBuffer
from middleware.storage.cache import DataCache
from middleware.storage.postgres import PostgresStorage
from middleware.storage.storagemanager import StorageManager


POSTGRES_CONFIG = {
    "dbname": "simulador",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": 5432,
}


def main():
    info("MAIN", "Iniciando middleware")

    cache = DataCache(maxsize=1000)

    info("CACHE", "Cache inicializado")

    postgres = PostgresStorage(
        dsn=(
            f"dbname={POSTGRES_CONFIG['dbname']} "
            f"user={POSTGRES_CONFIG['user']} "
            f"password={POSTGRES_CONFIG['password']} "
            f"host={POSTGRES_CONFIG['host']} "
            f"port={POSTGRES_CONFIG['port']}"
        )
    )

    buffer = SQLiteBuffer(db_path="buffer.db")

    storage = StorageManager(
        cache=cache,
        postgres=postgres,
        buffer=buffer,
        flush_interval=15,
    )

    opc = OpcUaServer(
        storage=storage,
        endpoint="opc.tcp://localhost:4840",
    )

    opc.start()

    storage.start()

    client = MQTTClient(storage)

    client.connect()

    info("MQTT", "Conectado")

    sleep(2)

    client.loop_forever()


if __name__ == "__main__":
    try:

        main()

    except KeyboardInterrupt:

        info("MAIN", "Middleware encerrado")

    except Exception as e:

        error("MAIN", f"Erro inesperado: {e}")