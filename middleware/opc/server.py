import asyncio

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

        SCREEN_MAIN: [
            ("GridPower", "grid", "active_power_kw"),
            ("ExtruderPower", "extruder", "power_kw"),
            ("CompressorPower", "aircompressor", "power_kw"),
        ],


        SCREEN_SUBSTATION: [
            ("Voltage", "grid", "voltage"),
            ("PowerFactor", "grid", "power_factor"),
            ("ActivePower", "grid", "active_power_kw"),

            ("VoltageHistory", "grid", "voltage", "history"),
            ("VoltageHistoryTimestamp", "grid", "timestamp", "history"),

            ("PowerFactorHistory", "grid", "power_factor", "history"),
            ("PowerFactorHistoryTimestamp", "grid", "timestamp", "history"),

            ("ActivePowerHistory", "grid", "active_power_kw", "history"),
            ("ActivePowerHistoryTimestamp", "grid", "timestamp", "history"),
        ],


        SCREEN_COMPRESSOR: [
            ("Current", "aircompressor", "current"),
            ("PowerFactor", "aircompressor", "power_factor"),
            ("Power", "aircompressor", "power_kw"),

            ("CurrentHistory", "aircompressor", "current", "history"),
            ("CurrentHistoryTimestamp", "aircompressor", "timestamp", "history"),

            ("PowerHistory", "aircompressor", "power_kw", "history"),
            ("PowerHistoryTimestamp", "aircompressor", "timestamp", "history"),
        ],


        SCREEN_EXTRUDER: [
            ("THD", "extruder", "current_thd"),
            ("Power", "extruder", "power_kw"),
            ("Temperature", "extruder", "panel_temperature"),

            ("THDHistory", "extruder", "current_thd", "history"),
            ("THDHistoryTimestamp", "extruder", "timestamp", "history"),

            ("PowerHistory", "extruder", "power_kw", "history"),
            ("PowerHistoryTimestamp", "extruder", "timestamp", "history"),

            ("TemperatureHistory", "extruder", "panel_temperature", "history"),
            ("TemperatureHistoryTimestamp", "extruder", "timestamp", "history"),
        ],
    }

    SCREEN_NAMES = {
        SCREEN_MAIN: "TelaPrincipal",
        SCREEN_SUBSTATION: "TelaSubestacao",
        SCREEN_COMPRESSOR: "TelaCompressor",
        SCREEN_EXTRUDER: "TelaExtrusora",
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
        self.screen = None

        self.active_screen_node = None
        self.active_screen_name_node = None

        self.tag_nodes = {}

        self._stop_event = threading.Event()
        self._thread = None
        self._loop = None

        self.current_screen = self.SCREEN_MAIN

    # ==================================================================
    # START
    # ==================================================================

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

    # ==================================================================
    # STOP
    # ==================================================================

    def stop(self):

        self._stop_event.set()

        if self._loop is not None:
            self._loop.call_soon_threadsafe(
                lambda: None
            )

        if self._thread is not None:
            self._thread.join(timeout=5)

    # ==================================================================
    # THREAD
    # ==================================================================

    def _thread_main(self):

        self._loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self._loop)

        try:

            self._loop.run_until_complete(
                self._run()
            )

        except Exception:

            print(
                "Servidor OPC UA encerrado com erro"
            )

        finally:

            self._loop.close()

            self._loop = None



    # ==================================================================
    # RUN
    # ==================================================================

    async def _run(self):

        self.server = Server()

        await self._init()

        print(
            f"OPC UA Server iniciado: {self.endpoint}"
        )

        async with self.server:

            while not self._stop_event.is_set():

                try:

                    await self._update()

                except Exception:

                    print(
                        "Erro durante atualização OPC UA"
                    )

                await asyncio.sleep(
                    self.update_interval
                )

        print(
            "OPC UA Server encerrado"
        )

    # ==================================================================
    # INIT
    # ==================================================================

    async def _init(self):

        await self.server.init()

        self.server.set_endpoint(
            self.endpoint
        )

        self.namespace_idx = (
            await self.server.register_namespace(
                "IndustrialSimulator"
            )
        )

        print(
            "Namespace:",
            self.namespace_idx
        )

        # --------------------------------------------------------------
        # Objects
        # --------------------------------------------------------------

        objects = self.server.nodes.objects

        # --------------------------------------------------------------
        # IndustrialSimulator
        # --------------------------------------------------------------

        self.plant = await objects.add_object(
            self.namespace_idx,
            "IndustrialSimulator"
        )

        # --------------------------------------------------------------
        # ActiveScreenID
        # --------------------------------------------------------------

        self.active_screen_node = (
            await self.plant.add_variable(
                self.namespace_idx,
                "ActiveScreenID",
                self.SCREEN_MAIN,
                ua.VariantType.Int32,
            )
        )

        # O E3 precisa poder escrever essa variável.

        await self.active_screen_node.set_writable()

        # --------------------------------------------------------------
        # ActiveScreenName
        # --------------------------------------------------------------

        self.active_screen_name_node = (
            await self.plant.add_variable(
                self.namespace_idx,
                "ActiveScreenName",
                self.SCREEN_NAMES[
                    self.SCREEN_MAIN
                ],
                ua.VariantType.String,
            )
        )

        # --------------------------------------------------------------
        # Screen
        # --------------------------------------------------------------

        self.screen = await self.plant.add_object(
            self.namespace_idx,
            "Screen"
        )

        # --------------------------------------------------------------
        # 20 Tags fixas
        # --------------------------------------------------------------

        for i in range(1, 11):

            tag_name = f"Tag{i:02d}"

            node = await self.screen.add_variable(
                self.namespace_idx,
                tag_name,
                0.0,
                ua.VariantType.Double,
            )

            self.tag_nodes[i] = node



    # ==================================================================
    # UPDATE
    # ==================================================================

    async def _update(self):

        # --------------------------------------------------------------
        # Descobre a tela atual
        # --------------------------------------------------------------

        screen_id = await (
            self.active_screen_node.read_value()
        )

        try:

            screen_id = int(screen_id)

        except (TypeError, ValueError):

            screen_id = self.SCREEN_MAIN

        # --------------------------------------------------------------
        # Tela inválida
        # --------------------------------------------------------------

        if screen_id not in self.SCREEN_CONFIG:

            screen_id = self.SCREEN_MAIN

            await self.active_screen_node.write_value(
                ua.Variant(
                    screen_id,
                    ua.VariantType.Int32
                )
            )

        # --------------------------------------------------------------
        # Atualiza nome
        # --------------------------------------------------------------

        screen_name = self.SCREEN_NAMES[
            screen_id
        ]

        await self.active_screen_name_node.write_value(
            ua.Variant(
                screen_name,
                ua.VariantType.String
            )
        )

        self.current_screen = screen_id

        # --------------------------------------------------------------
        # Atualiza Tags
        # --------------------------------------------------------------

        await self._update_screen(
            screen_id
        )

    # ==================================================================
    # UPDATE SCREEN
    # ==================================================================

    async def _update_screen(
        self,
        screen_id: int,
    ):

        config = self.SCREEN_CONFIG[
            screen_id
        ]

        for i in range(1, 11):

            node = self.tag_nodes[i]

            await node.write_value(
                ua.Variant(
                    0.0,
                    ua.VariantType.Double
                )
            )

        # --------------------------------------------------------------
        # Descobre quais fontes são necessárias
        # --------------------------------------------------------------

        sources = set()

        for item in config:

            source = item[1]

            sources.add(source)

        # --------------------------------------------------------------
        # Carrega os dados necessários
        # --------------------------------------------------------------

        data_cache = {}

        for source in sources:

            try:

                data = self.storage.get_data(
                    source,
                    limit=self.HISTORY_SIZE,
                )

                data_cache[source] = data

            except Exception:

                print(
                    "Erro ao obter dados do StorageManager: %s",
                    source,
                )

                data_cache[source] = []

        # --------------------------------------------------------------
        # Preenche Tags
        # --------------------------------------------------------------

        for index, definition in enumerate(
            config,
            start=1,
        ):

            tag_node = self.tag_nodes[
                index
            ]

            name = definition[0]
            source = definition[1]
            field = definition[2]

            is_history = (
                len(definition) >= 4
                and definition[3] == "history"
            )

            data = data_cache.get(
                source,
                []
            )

            # ----------------------------------------------------------
            # TAG NORMAL
            # ----------------------------------------------------------

            if not is_history:

                value = self._get_latest_value(
                    data,
                    field,
                )

                await self._write_scalar(
                    tag_node,
                    value,
                )

            # ----------------------------------------------------------
            # TAG HISTÓRICA
            # ----------------------------------------------------------

            else:

                values = self._get_history(
                    data,
                    field,
                )

                await self._write_array(
                    tag_node,
                    values,
                )

    # ==================================================================
    # GET LATEST
    # ==================================================================

    @staticmethod
    def _get_latest_value(
        data: list,
        field: str,
    ):

        if not data:

            return 0.0

        latest = data[-1]

        value = latest.get(
            field,
            0.0
        )

        if value is None:

            return 0.0

        return value

    # ==================================================================
    # GET HISTORY
    # ==================================================================

    def _get_history(
        self,
        data: list,
        field: str,
    ) -> list:

        if not data:

            return [
                0.0
            ] * self.HISTORY_SIZE

        values = []

        for item in data[-self.HISTORY_SIZE:]:

            value = item.get(
                field,
                0.0
            )

            if value is None:

                value = 0.0

            try:

                value = float(value)

            except (TypeError, ValueError):

                value = 0.0

            values.append(
                value
            )

        # --------------------------------------------------------------
        # Completa até 100 posições
        # --------------------------------------------------------------

        if len(values) < self.HISTORY_SIZE:

            missing = (
                self.HISTORY_SIZE
                - len(values)
            )

            values = (
                [0.0] * missing
                + values
            )

        return values

    # ==================================================================
    # WRITE SCALAR
    # ==================================================================

    async def _write_scalar(
        self,
        node,
        value,
    ):

        try:

            value = float(value)

        except (TypeError, ValueError):

            value = 0.0

        await node.write_value(
            ua.Variant(
                value,
                ua.VariantType.Double
            )
        )

    # ==================================================================
    # WRITE ARRAY
    # ==================================================================

    async def _write_array(
        self,
        node,
        values: list,
    ):

        values = [
            float(value)
            for value in values
        ]

        await node.write_value(
            ua.Variant(
                values,
                ua.VariantType.Double
            )
        )