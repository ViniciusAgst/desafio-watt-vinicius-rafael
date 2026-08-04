import random
import time

from assets.device import Device, State


class Grid(Device):

    NOMINAL_VOLTAGE = 380.0

    def __init__(self, name: str):
        super().__init__(name)

        self.voltage = self.NOMINAL_VOLTAGE
        self.power_factor = 0.95
        self.active_power = 0.0  # kW

        self._fault = False
        self._fault_type = None
        self._fault_end = 0.0

    def start(self):
        self.state = State.RUNNING

    def stop(self):
        self.state = State.STOPPED

    def update(self, devices=None):

        if self.state != State.RUNNING:
            return

        if devices is not None:
            self.active_power = sum(
                getattr(device, "power", 0.0)
                for device in devices
            )

        if self._fault:

            if time.time() >= self._fault_end:
                self.stop_fault()

            else:
                self.voltage = 350 + random.uniform(-2, 2)

        else:
            self.voltage = (
                self.NOMINAL_VOLTAGE
                + random.uniform(-2, 2)
            )

        self.power_factor = random.uniform(0.94, 0.97)


    def start_fault(self):
        if self._fault:
            return

        duration = random.uniform(5, 15)

        self._fault = True
        self._fault_type = "voltage_sag"
        self._fault_end = time.time() + duration


    def stop_fault(self):
        self._fault = False
        self._fault_type = None
        self.voltage = self.NOMINAL_VOLTAGE


    def get_data(self):
        return {
            "name": self.name,
            "state": self.state.value,
            "voltage": round(self.voltage, 2),
            "power_factor": round(self.power_factor, 3),
            "active_power_kw": round(self.active_power, 2),
            "fault": self._fault,
            "fault_type": self._fault_type
        }