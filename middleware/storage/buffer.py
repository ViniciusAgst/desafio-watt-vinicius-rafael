import json
import sqlite3
import threading

from logger import info, warn, error, debug


class SQLiteBuffer:

    def __init__(self, db_path: str = "buffer.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()


    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)


    def _init_schema(self):
        try:
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

            info("BUFFER", f"SQLite inicializado: {self.db_path}")

        except Exception as exc:
            error("BUFFER", f"Falha ao inicializar SQLite: {exc}")
            raise


    def add(self, name: str, tipo: str, timestamp: float, state: str, dados: dict) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO buffer_medicoes (name, tipo, timestamp, state, dados)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (name, tipo, timestamp, state, json.dumps(dados)),
                )

            debug("BUFFER", f"Medida armazenada: {name}")

        except Exception as exc:
            error("BUFFER", f"Falha ao armazenar medida de {name}: {exc}")
            raise


    def get_all(self) -> list:
        try:
            with self._lock, self._connect() as conn:
                cur = conn.execute(
                    "SELECT name, tipo, timestamp, state, dados FROM buffer_medicoes ORDER BY id ASC;"
                )
                rows = cur.fetchall()

            result = [
                {
                    "name": r[0],
                    "tipo": r[1],
                    "timestamp": r[2],
                    "state": r[3],
                    "dados": json.loads(r[4]),
                }
                for r in rows
            ]

            debug("BUFFER", f"Leituras recuperadas: {len(result)}")

            return result

        except Exception as exc:
            error("BUFFER", f"Falha ao recuperar leituras: {exc}")
            raise


    def clear(self) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute("DELETE FROM buffer_medicoes;")

            info("BUFFER", "Buffer esvaziado")

        except Exception as exc:
            error("BUFFER", f"Falha ao limpar buffer: {exc}")
            raise


    def count(self) -> int:
        try:
            with self._lock, self._connect() as conn:
                cur = conn.execute("SELECT COUNT(*) FROM buffer_medicoes;")
                return cur.fetchone()[0]

        except Exception as exc:
            error("BUFFER", f"Falha ao consultar buffer: {exc}")
            return 0