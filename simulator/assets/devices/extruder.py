import random

from assets.device import Device, State


class Extruder(Device):

    NOMINAL_POWER = 45.0  # kW

    def __init__(self, name: str):
        super().__init__(name)

        self.power = 0.0
        self.load = 0.0

        self.current_thd = 0.0
        self.panel_temperature = 25.0

        self._fault = False
        self._fault_type = None

    def start(self):
        self.state = State.RUNNING

    def stop(self):
        self.state = State.STOPPED
        self.power = 0.0
        self.load = 0.0

    def update(self):

        if self.state != State.RUNNING:
            return

        self.load = random.uniform(0.6, 1.0)

        self.power = self.NOMINAL_POWER * self.load


        if self._fault:
            self.current_thd = random.uniform(30.0, 40.0)
        else:
            self.current_thd = random.uniform(15.0, 25.0)


        target_temp = (
            30
            + self.load * 20
            + (self.current_thd - 15) * 0.8
        )

        if self._fault:
            self.panel_temperature += (
                target_temp - self.panel_temperature
            ) * 0.1
        else:
            self.panel_temperature += (
                target_temp - self.panel_temperature
            ) * 0.05


    def start_fault(self):

        if self._fault:
            return

        self._fault = True
        self._fault_type = "high_current_thd"


    def stop_fault(self):

        self._fault = False
        self._fault_type = None


    def get_data(self):
        return {
            "name": self.name,
            "state": self.state.value,
            "power_kw": round(self.power, 2),
            "load": round(self.load * 100, 1),
            "current_thd": round(self.current_thd, 2),
            "panel_temperature": round(self.panel_temperature, 1),
            "fault": self._fault,
            "fault_type": self._fault_type
        }