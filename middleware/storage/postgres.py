
import psycopg2
import psycopg2.extras


class PostgresStorage:

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._conn = None


    def try_connect(self) -> bool:
        try:
            self._conn = psycopg2.connect(self.dsn)
            self._conn.autocommit = True
            self._ensure_schema()
            print("[Postgres] Conectado em %s", self._safe_dsn())
            return True

        except Exception as exc:
            print("[Postgres] Indisponível: %s", exc)
            self._conn = None
            return False


    def _safe_dsn(self) -> str:
        return self.dsn.split("password=")[0] + "password=***"

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            raise ConnectionError("Sem conexão ativa com o Postgres")
        return self._conn



    def _ensure_schema(self):
        with self._conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ativos (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL,
                    dados_estaticos JSONB NOT NULL DEFAULT '{}'::jsonb,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS medicoes (
                    id BIGSERIAL PRIMARY KEY,
                    ativo_id INTEGER NOT NULL REFERENCES ativos(id),
                    timestamp DOUBLE PRECISION NOT NULL,
                    state TEXT,
                    dados JSONB NOT NULL,
                    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_medicoes_ativo_ts
                ON medicoes (ativo_id, timestamp DESC);
                """
            )


    def upsert_asset(self, name: str, tipo: str, dados_estaticos: dict = None) -> int:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ativos (name, tipo, dados_estaticos)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET tipo = EXCLUDED.tipo
                RETURNING id;
                """,
                (name, tipo, psycopg2.extras.Json(dados_estaticos or {})),
            )
            return cur.fetchone()[0]

    def insert_measurement(self, ativo_id: int, timestamp: float, state: str, dados: dict) -> None:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO medicoes (ativo_id, timestamp, state, dados)
                VALUES (%s, %s, %s, %s);
                """,
                (ativo_id, timestamp, state, psycopg2.extras.Json(dados)),
            )



    def get_measurements(self, tipo: str, limit: int = 100, before_timestamp: float = None) -> list:
        conn = self._get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if before_timestamp is not None:
                cur.execute(
                    """
                    SELECT a.name, m.timestamp, m.state, m.dados
                    FROM medicoes m
                    JOIN ativos a ON a.id = m.ativo_id
                    WHERE a.tipo = %s AND m.timestamp < %s
                    ORDER BY m.timestamp DESC
                    LIMIT %s;
                    """,
                    (tipo, before_timestamp, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT a.name, m.timestamp, m.state, m.dados
                    FROM medicoes m
                    JOIN ativos a ON a.id = m.ativo_id
                    WHERE a.tipo = %s
                    ORDER BY m.timestamp DESC
                    LIMIT %s;
                    """,
                    (tipo, limit),
                )
            rows = cur.fetchall()

        result = []
        for row in reversed(rows):  # devolve em ordem crescente (mais antigo -> mais novo)
            item = {"timestamp": row["timestamp"], "name": row["name"], "state": row["state"]}
            item.update(row["dados"])
            result.append(item)
        return result



    def is_available(self) -> bool:
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return True
        except Exception:
            return False