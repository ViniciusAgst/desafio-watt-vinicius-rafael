import random
import time

from assets.device import Device, State

class Extruder(Device):

    NOMINAL_POWER = 45.0

    def __init__(self, name: str):
        super().__init__(name)

        self.power = 0.0

        self.current_thd = 0.0
        self.panel_temperature = 25.0

    def start(self):
        self.state = State.RUNNING

    def stop(self):
        self.state = State.STOPPED
        self.power = 0.0

    def update(self):

        if self.state != State.RUNNING:
            return

        load = random.uniform(0.7, 1.0)

        self.power = self.NOMINAL_POWER * load

        if self.state == State.FAULT:
            self.current_thd = random.uniform(30.0, 40.0)
        else:
            self.current_thd = random.uniform(15.0, 25.0)

        target_temp = (
            30
            + load * 20
            + (self.current_thd - 15) * 0.8
        )

        if self.state == State.FAULT:
            self.panel_temperature += (
                target_temp - self.panel_temperature
            ) * 0.1

        else:
            self.panel_temperature += (
                target_temp - self.panel_temperature
            ) * 0.05


    def start_fault(self):

        if self.state == State.FAULT:
            return

        self.state = State.FAULT


    def stop_fault(self):

        self.state = State.RUNNING


    def get_data(self):
        return {
            "timestamp": time.time(),
            "name": self.name,
            "state": self.state.value,
            "power_kw": round(self.power, 2),
            "current_thd": round(self.current_thd, 2),
            "panel_temperature": round(self.panel_temperature, 1)
        }