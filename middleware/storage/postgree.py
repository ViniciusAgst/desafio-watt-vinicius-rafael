import psycopg2
from psycopg2.extras import Json


class PostgreSQL:


    def __init__(self):

        self.conn = psycopg2.connect(

            host="localhost",
            database="industrial",
            user="postgres",
            password="postgres",
            port=5432
        )


    def insert(
        self,
        topic,
        payload
    ):

        cursor = self.conn.cursor()


        cursor.execute(
            """
            INSERT INTO measurements
            (
                topic,
                data
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                topic,
                Json(payload)
            )
        )


        self.conn.commit()

        cursor.close()