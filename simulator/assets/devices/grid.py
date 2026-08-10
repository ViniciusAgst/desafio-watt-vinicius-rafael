import random
import time

from assets.device import Device, State


class Grid(Device):

    NOMINAL_VOLTAGE = 380.0

    def __init__(self, name: str):
        super().__init__(name)

        self.voltage = self.NOMINAL_VOLTAGE
        self.power_factor = 0.95
        self.active_power = 0.0

    def start(self):
        self.state = State.RUNNING

    def stop(self):
        self.state = State.STOPPED

    def update(self, devices=None):

        if self.state != State.RUNNING and self.state != State.FAULT:
            return

        if devices is not None:
            self.active_power = sum(
                getattr(device, "power", 0.0)
                for device in devices
            )

        if self.state == State.FAULT:
            self.voltage = (350 + random.uniform(-2, 2))

        else:
            self.voltage = (
                self.NOMINAL_VOLTAGE
                + random.uniform(-2, 2)
            )

        self.power_factor = random.uniform(0.94, 0.97)


    def start_fault(self):
        if self.state == State.FAULT:
            return

        self.state = State.FAULT


    def stop_fault(self):
        self.state = State.RUNNING

        self.voltage = self.NOMINAL_VOLTAGE

    def get_data(self):
        return {
            "timestamp": time.time(),
            "name": self.name,
            "state": self.state.value,
            "voltage": round(self.voltage, 2),
            "power_factor": round(self.power_factor, 3),
            "active_power_kw": round(self.active_power, 2)
        }