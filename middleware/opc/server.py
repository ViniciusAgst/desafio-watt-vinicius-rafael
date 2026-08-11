import asyncio
import json
import threading
from typing import Optional

from asyncua import Server, ua


class OpcUaServer:

    HISTORY_SIZE = 100

    SCREEN_MAIN = 1
    SCREEN_SUBSTATION = 2
    SCREEN_COMPRESSOR = 3
    SCREEN_EXTRUDER = 4

    SCREEN_CONFIG = {
        SCREEN_MAIN: {
            "name": "TelaPrincipal",
            "scalars": {
                "GridPower": ("grid", "active_power_kw"),
                "ExtruderPower": ("extruder", "power_kw"),
                "CompressorPower": ("aircompressor", "power_kw"),
            },
        },
        SCREEN_SUBSTATION: {
            "name": "TelaSubestacao",
            "scalars": {
                "Voltage": ("grid", "voltage"),
                "PowerFactor": ("grid", "power_factor"),
                "ActivePower": ("grid", "active_power_kw"),
            },
            "history": {
                "timestamp": ("grid", "timestamp"),
                "tags": [
                    ("Voltage", "grid", "voltage"),
                    ("PowerFactor", "grid", "power_factor"),
                    ("ActivePower", "grid", "active_power_kw"),
                ],
            },
        },
        SCREEN_COMPRESSOR: {
            "name": "TelaCompressor",
            "scalars": {
                "Current": ("aircompressor", "current"),
                "PowerFactor": ("aircompressor", "power_factor"),
                "Power": ("aircompressor", "power_kw"),
            },
            "history": {
                "timestamp": ("aircompressor", "timestamp"),
                "tags": [
                    ("Current", "aircompressor", "current"),
                    ("PowerFactor", "aircompressor", "power_factor"),
                    ("Power", "aircompressor", "power_kw"),
                ],
            },
        },
        SCREEN_EXTRUDER: {
            "name": "TelaExtrusora",
            "scalars": {
                "THD": ("extruder", "current_thd"),
                "Power": ("extruder", "power_kw"),
                "Temperature": ("extruder", "panel_temperature"),
            },
            "history": {
                "timestamp": ("extruder", "timestamp"),
                "tags": [
                    ("THD", "extruder", "current_thd"),
                    ("Power", "extruder", "power_kw"),
                    ("Temperature", "extruder", "panel_temperature"),
                ],
            },
        },
    }

    def __init__(
        self,
        storage,
        endpoint: str = "opc.tcp://0.0.0.0:4840",
        update_interval: float = 1.0,
    ):
        self.storage = storage
        self.endpoint = endpoint
        self.update_interval = update_interval

        self.server: Optional[Server] = None
        self.namespace_idx = None

        self.plant = None
        self.historicos = None

        self.active_screen_node = None
        self.active_screen_name_node = None

        self.screen_nodes = {}
        self.history_nodes = {}

        self._stop_event = threading.Event()
        self._thread = None
        self._loop = None

        self.current_screen = self.SCREEN_MAIN

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._thread_main,
            name="OPC-UA-Server",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._loop is not None:
            self._loop.call_soon_threadsafe(lambda: None)
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _thread_main(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run())
        except Exception as exception:
            print(f"Servidor OPC UA encerrado com erro: {exception}")
        finally:
            self._loop.close()
            self._loop = None

    async def _run(self):
        self.server = Server()
        await self._init()
        print(f"OPC UA Server iniciado: {self.endpoint}")

        async with self.server:
            while not self._stop_event.is_set():
                try:
                    await self._update()
                except Exception as exception:
                    print(f"Erro durante atualização OPC UA: {exception}")
                await asyncio.sleep(self.update_interval)

        print("OPC UA Server encerrado")

    async def _init(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)

        self.namespace_idx = await self.server.register_namespace(
            "IndustrialSimulator"
        )

        objects = self.server.nodes.objects
        self.plant = await objects.add_object(
            self.namespace_idx,
            "IndustrialSimulator",
        )

        self.active_screen_node = await self.plant.add_variable(
            self.namespace_idx,
            "ActiveScreenID",
            ua.Variant(self.SCREEN_MAIN, ua.VariantType.Int32),
        )
        await self.active_screen_node.set_writable()

        self.active_screen_name_node = await self.plant.add_variable(
            self.namespace_idx,
            "ActiveScreenName",
            ua.Variant(
                self.SCREEN_CONFIG[self.SCREEN_MAIN]["name"],
                ua.VariantType.String,
            ),
        )

        # Variáveis escalares por tela
        for screen_id, config in self.SCREEN_CONFIG.items():
            screen_node = await self.plant.add_object(
                self.namespace_idx,
                config["name"],
            )

            self.screen_nodes[screen_id] = {}

            for tag_name in config["scalars"]:
                node = await screen_node.add_variable(
                    self.namespace_idx,
                    tag_name,
                    ua.Variant(0.0, ua.VariantType.Double),
                )
                self.screen_nodes[screen_id][tag_name] = node

        # HISTÓRICOS: Cada Tag1, Tag2, etc., é uma Tag String contendo JSON de um único array
        self.historicos = await self.plant.add_object(
            self.namespace_idx,
            "Historicos",
        )

        max_history_tags = max(
            len(config.get("history", {}).get("tags", [])) + 1
            for config in self.SCREEN_CONFIG.values()
        )

        default_empty_json = json.dumps([0.0] * self.HISTORY_SIZE)

        for index in range(1, max_history_tags + 1):
            tag_name = f"Tag{index}"

            # Cria nó como STRING simples (Escalar)
            node = await self.historicos.add_variable(
                self.namespace_idx,
                tag_name,
                ua.Variant(default_empty_json, ua.VariantType.String),
            )
            self.history_nodes[tag_name] = node

    async def _update(self):
        screen_id = await self.active_screen_node.read_value()

        try:
            screen_id = int(screen_id)
        except (TypeError, ValueError):
            screen_id = self.SCREEN_MAIN

        if screen_id not in self.SCREEN_CONFIG:
            screen_id = self.SCREEN_MAIN
            await self.active_screen_node.write_value(
                ua.Variant(screen_id, ua.VariantType.Int32)
            )

        screen_name = self.SCREEN_CONFIG[screen_id]["name"]
        await self.active_screen_name_node.write_value(
            ua.Variant(screen_name, ua.VariantType.String)
        )

        self.current_screen = screen_id

        await self._update_scalars()
        await self._update_history(screen_id)

    async def _update_scalars(self):
        sources = set()
        for config in self.SCREEN_CONFIG.values():
            for source, _ in config["scalars"].values():
                sources.add(source)

        data_cache = await self._load_data(sources)

        for screen_id, config in self.SCREEN_CONFIG.items():
            for tag_name, (source, field) in config["scalars"].items():
                data = data_cache.get(source, [])
                value = self._get_latest_value(data, field)
                node = self.screen_nodes[screen_id][tag_name]
                await self._write_scalar(node, value)

    async def _update_history(self, screen_id: int):
        config = self.SCREEN_CONFIG[screen_id]
        history_config = config.get("history")

        if history_config is None:
            empty_json = json.dumps([0.0] * self.HISTORY_SIZE)
            for node in self.history_nodes.values():
                await node.write_value(
                    ua.Variant(empty_json, ua.VariantType.String)
                )
            return

        timestamp_source, timestamp_field = history_config["timestamp"]
        sources = {timestamp_source}

        for _, source, _ in history_config["tags"]:
            sources.add(source)

        data_cache = await self._load_data(sources)

        # Tag1 = Timestamp
        timestamp_data = data_cache.get(timestamp_source, [])
        timestamps = self._get_history(timestamp_data, timestamp_field)
        await self.history_nodes["Tag1"].write_value(
            ua.Variant(json.dumps(timestamps), ua.VariantType.String)
        )

        active_tags = {"Tag1"}

        # Tag2, Tag3, Tag4 = Tags de Dados da Tela Ativa
        for index, (_, source, field) in enumerate(
            history_config["tags"], start=2
        ):
            tag_name = f"Tag{index}"
            active_tags.add(tag_name)

            data = data_cache.get(source, [])
            values = self._get_history(data, field)

            await self.history_nodes[tag_name].write_value(
                ua.Variant(json.dumps(values), ua.VariantType.String)
            )

        # Zera tags que não estiverem sendo utilizadas pela tela atual
        empty_json = json.dumps([0.0] * self.HISTORY_SIZE)
        for tag_name, node in self.history_nodes.items():
            if tag_name not in active_tags:
                await node.write_value(
                    ua.Variant(empty_json, ua.VariantType.String)
                )

    async def _load_data(self, sources):
        data_cache = {}
        for source in sources:
            try:
                data_cache[source] = self.storage.get_data(
                    source, limit=self.HISTORY_SIZE
                )
            except Exception as exception:
                print(
                    f"Erro ao obter dados do StorageManager: {source}: {exception}"
                )
                data_cache[source] = []
        return data_cache

    @staticmethod
    def _get_latest_value(data: list, field: str):
        if not data:
            return 0.0
        value = data[-1].get(field, 0.0)
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _get_history(self, data: list, field: str) -> list:
        if not data:
            return [0.0] * self.HISTORY_SIZE

        values = []
        for item in data[-self.HISTORY_SIZE:]:
            value = item.get(field, 0.0)
            if value is None:
                value = 0.0
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0
            values.append(value)

        if len(values) < self.HISTORY_SIZE:
            missing = self.HISTORY_SIZE - len(values)
            values = [0.0] * missing + values

        return values

    @staticmethod
    async def _write_scalar(node, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0

        await node.write_value(
            ua.Variant(value, ua.VariantType.Double)
        )