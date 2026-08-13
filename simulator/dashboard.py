from flask import Flask, render_template, jsonify

from common.logger import info


class Dashboard:

    def __init__(self, grid, compressor, extruder):

        self.grid = grid
        self.compressor = compressor
        self.extruder = extruder

        self.app = Flask(__name__)

        self.routes()

    def routes(self):

        @self.app.route("/")
        def index():
            return render_template("index.html")


        @self.app.route("/data")
        def data():
            return jsonify({

                "grid": {
                    "voltage": self.grid.voltage
                },

                "compressor": {
                    "current": self.compressor.current
                },

                "extruder": {
                    "current_thd": self.extruder.current_thd
                }

            })


        @self.app.post("/grid/start")
        def grid_start():
            self.grid.start_fault()
            return jsonify({"status": "ok", "device": "grid", "action": "start"})

        @self.app.post("/grid/stop")
        def grid_stop():
            self.grid.stop_fault()
            return jsonify({"status": "ok", "device": "grid", "action": "stop"})


        @self.app.post("/compressor/start")
        def compressor_start():
            self.compressor.start_fault()
            return jsonify({"status": "ok", "device": "compressor", "action": "start"})

        @self.app.post("/compressor/stop")
        def compressor_stop():
            self.compressor.stop_fault()
            return jsonify({"status": "ok", "device": "compressor", "action": "stop"})


        @self.app.post("/extruder/start")
        def extruder_start():
            self.extruder.start_fault()
            return jsonify({"status": "ok", "device": "extruder", "action": "start"})

        @self.app.post("/extruder/stop")
        def extruder_stop():
            self.extruder.stop_fault()
            return jsonify({"status": "ok", "device": "extruder", "action": "stop"})


    def start(self):
        info("DASHBOARD", "Dashboard iniciando em http://localhost:5000")

        self.app.run(
            host="0.0.0.0",
            port=5000
        )