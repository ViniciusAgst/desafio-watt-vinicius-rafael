import sqlite3
import json


class Buffer:

    def __init__(self):
        self.conn = sqlite3.connect(
            "buffer.db",
            check_same_thread=False
        )

        self.create_table()


    def create_table(self):

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS queue (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            topic TEXT,

            payload TEXT
        )
        """)

        self.conn.commit()


    def add(self, topic, payload):

        self.conn.execute(
            """
            INSERT INTO queue(topic, payload)
            VALUES (?, ?)
            """,
            (
                topic,
                json.dumps(payload)
            )
        )

        self.conn.commit()


    def get_all(self):

        cursor = self.conn.execute(
            """
            SELECT id, topic, payload
            FROM queue
            ORDER BY id
            """
        )

        return cursor.fetchall()


    def remove(self, id):

        self.conn.execute(
            """
            DELETE FROM queue
            WHERE id=?
            """,
            (id,)
        )

        self.conn.commit()