
from middleware.connection.mqttclient import MQTTClient
from middleware.storage.buffer import SQLiteBuffer
from middleware.storage.cache import DataCache
from middleware.storage.postgres import PostgresStorage
from middleware.storage.storagemanager import StorageManager


def main():
    cache = DataCache(maxsize=1000)

    postgres = PostgresStorage(dsn="dbname=simulador user=postgres password=root host=localhost port=5432")

    buffer = SQLiteBuffer(db_path="buffer.db")

    storage = StorageManager(
        cache=cache,
        postgres=postgres,
        buffer=buffer,
        flush_interval=15,
    )

    storage.start()

    client = MQTTClient(storage)
    client.connect()

    client.loop_forever()


if __name__ == "__main__":
    main()