import json

import sqlite3
import threading


class SQLiteBuffer:

    def __init__(self, db_path: str = "buffer.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()



    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)



    def _init_schema(self):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS buffer_medicoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    state TEXT,
                    dados TEXT NOT NULL,
                    criado_em REAL DEFAULT (strftime('%s','now'))
                );
                """
            )



    def add(self, name: str, tipo: str, timestamp: float, state: str, dados: dict) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO buffer_medicoes (name, tipo, timestamp, state, dados)
                VALUES (?, ?, ?, ?, ?);
                """,
                (name, tipo, timestamp, state, json.dumps(dados)),
            )



    def get_all(self) -> list:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "SELECT name, tipo, timestamp, state, dados FROM buffer_medicoes ORDER BY id ASC;"
            )
            rows = cur.fetchall()
        return [
            {
                "name": r[0],
                "tipo": r[1],
                "timestamp": r[2],
                "state": r[3],
                "dados": json.loads(r[4]),
            }
            for r in rows
        ]



    def clear(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM buffer_medicoes;")



    def count(self) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM buffer_medicoes;")
            return cur.fetchone()[0]