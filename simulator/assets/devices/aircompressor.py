import random
import time

from assets.device import Device, State


class AirCompressor(Device):

    NOMINAL_CURRENT = 45.0
    NOMINAL_POWER = 30.0

    def __init__(self, name: str):
        super().__init__(name)

        self.power = 0.0

        self.current = 0.0
        self.power_factor = 0.88

        self._starting_until = 0.0
        self._cycle_until = 0.0

    def start(self):

        if self.state != State.STOPPED:
            return

        self.state = State.STARTING

        self._starting_until = (
            time.time() + random.uniform(2, 4)
        )

    def stop(self):

        self.state = State.STOPPED
        self.current = 0.0
        self.power = 0.0

        self._cycle_until = (
            time.time() + random.uniform(10, 20)
        )

    def update(self):

        now = time.time()

        if self.state == State.STOPPED:

            if now >= self._cycle_until:
                self.start()

            return

        if self.state == State.FAULT:

            self.current = (
                self.NOMINAL_CURRENT *
                random.uniform(7.0, 9.0)
            )

            self.power_factor = random.uniform(
                0.65, 0.72
            )

            self.power = (
                self.NOMINAL_POWER *
                random.uniform(1.15, 1.35)
            )

            return

        if self.state == State.STARTING:

            self.current = (
                self.NOMINAL_CURRENT *
                random.uniform(5.0, 7.0)
            )

            self.power_factor = random.uniform(
                0.68, 0.72
            )

            self.power = (
                self.NOMINAL_POWER *
                random.uniform(0.9, 1.2)
            )

            if now >= self._starting_until:

                self.state = State.RUNNING

                self._cycle_until = (
                    now + random.uniform(30, 60)
                )

            return

        if self.state == State.RUNNING:

            self.current = (
                self.NOMINAL_CURRENT +
                random.uniform(-2, 2)
            )

            self.power_factor = random.uniform(
                0.87, 0.89
            )

            self.power = (
                self.NOMINAL_POWER +
                random.uniform(-1, 1)
            )

            if now >= self._cycle_until:
                self.stop()

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
            "current": round(self.current, 1),
            "power_factor": round(self.power_factor, 2),
            "power_kw": round(self.power, 2)
        }