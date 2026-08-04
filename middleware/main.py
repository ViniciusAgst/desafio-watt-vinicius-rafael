import json

from middleware.client.mqttclient import MQTTClient
from middleware.storage.buffer import Buffer
from middleware.storage.postgree import PostgreSQL

buffer = Buffer()

try:
    database = PostgreSQL()
    print("PostgreSQL conectado")

except Exception:
    database = None
    print("PostgreSQL indisponível")



def save_data(topic, payload):

    global database

    try:

        if database is None:
            database = PostgreSQL()


        database.insert(
            topic,
            payload
        )

        print(
            "Salvo no PostgreSQL:",
            topic
        )

        sync_buffer()


    except Exception:

        print(
            "Banco indisponível, usando buffer"
        )

        buffer.add(
            topic,
            payload
        )



def sync_buffer():

    global database

    items = buffer.get_all()

    for item in items:

        id, topic, payload = item

        try:

            database.insert(
                topic,
                json.loads(payload)
            )

            buffer.remove(id)

            print(
                "Buffer sincronizado:",
                topic
            )


        except Exception:

            break



def on_message(client, userdata, msg):

    payload = json.loads(
        msg.payload.decode()
    )


    save_data(
        msg.topic,
        payload
    )



mqtt = MQTTClient(
    on_message
)


mqtt.connect()

mqtt.subscribe()


print(
    "Coletor iniciado"
)

mqtt.loop()