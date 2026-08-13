import threading

from common.logger import info, warn, error, debug
from middleware.storage.buffer import SQLiteBuffer
from middleware.storage.cache import DataCache
from middleware.storage.postgres import PostgresStorage

_CAMPOS_COMUNS = ("name", "state", "timestamp")


class StorageManager:

    def __init__(
        self,
        cache: DataCache,
        postgres: PostgresStorage,
        buffer: SQLiteBuffer,
        flush_interval: int = 15,
    ):
        self.cache = cache
        self.postgres = postgres
        self.buffer = buffer
        self.flush_interval = flush_interval

        self._asset_ids = {}
        self._postgres_available = False

        self._stop_event = threading.Event()
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True
        )


    def start(self):
        self._postgres_available = self.postgres.try_connect()

        if self._postgres_available:
            info("STORAGE", "Usando PostGres...")

        else:
            warn(
                "STORAGE",
                "Postgres indisponível - usando buffer SQLite"
            )

        self._flush_thread.start()

        debug("STORAGE", "Thread de sincronização iniciada")


    def stop(self):
        info("STORAGE", "Encerrando Storage Manager")

        self._stop_event.set()
        self._flush_thread.join(timeout=5)

        info("STORAGE", "Storage Manager encerrado")


    def put(self, source: str, data: dict) -> None:
        self.cache.put(source, data)

        name = data.get("name", source)
        state = data.get("state")
        timestamp = data.get("timestamp")

        dados_extra = {
            k: v
            for k, v in data.items()
            if k not in _CAMPOS_COMUNS
        }

        if not self._postgres_available:
            self.buffer.add(
                name,
                source,
                timestamp,
                state,
                dados_extra
            )

            debug(
                "STORAGE",
                f"Medida armazenada no buffer: {name}"
            )

            return

        try:
            ativo_id = self._ensure_asset(name, source)

            self.postgres.insert_measurement(
                ativo_id,
                timestamp,
                state,
                dados_extra
            )

        except Exception as exc:
            warn(
                "STORAGE",
                f"Falha no Postgres - usando buffer: {exc}"
            )

            self._postgres_available = False

            self.buffer.add(
                name,
                source,
                timestamp,
                state,
                dados_extra
            )


    def _ensure_asset(self, name: str, tipo: str) -> int:
        if name not in self._asset_ids:
            self._asset_ids[name] = self.postgres.upsert_asset(
                name,
                tipo
            )

            debug(
                "STORAGE",
                f"Ativo registrado: {name}"
            )

        return self._asset_ids[name]


    def _flush_loop(self):
        while not self._stop_event.is_set():

            if not self._postgres_available:
                self._postgres_available = self.postgres.try_connect()

                if self._postgres_available:
                    info(
                        "STORAGE",
                        "Postgres voltou - sincronizando buffer"
                    )

            if self._postgres_available:
                self._flush_buffer()

            self._stop_event.wait(self.flush_interval)


    def _flush_buffer(self):
        pendentes = self.buffer.get_all()

        if not pendentes:
            return

        debug(
            "STORAGE",
            f"Iniciando sincronização de {len(pendentes)} registro(s)"
        )

        try:
            for row in pendentes:
                ativo_id = self._ensure_asset(
                    row["name"],
                    row["tipo"]
                )

                self.postgres.insert_measurement(
                    ativo_id,
                    row["timestamp"],
                    row["state"],
                    row["dados"]
                )

            self.buffer.clear()

            info(
                "STORAGE",
                f"{len(pendentes)} registro(s) sincronizados"
            )

        except Exception as exc:
            warn(
                "STORAGE",
                f"Postgres caiu durante sincronização: {exc}"
            )

            self._postgres_available = False


    def get_data(self, source: str, limit: int = 100) -> list:
        cached = self.cache.snapshot(source, limit)

        if len(cached) >= limit:
            return cached[-limit:]

        faltam = limit - len(cached)

        timestamp_mais_antigo = (
            cached[0]["timestamp"]
            if cached
            else None
        )

        try:
            historico = self.postgres.get_measurements(
                source,
                limit=faltam,
                before_timestamp=timestamp_mais_antigo
            )

        except Exception as exc:
            debug(
                "STORAGE",
                f"Não foi possível consultar Postgres: {exc}"
            )

            historico = []

        return historico + cached