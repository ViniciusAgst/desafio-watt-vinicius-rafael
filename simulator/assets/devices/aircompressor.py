import random
import time

from assets.device import Device, State


class AirCompressor(Device):

    NOMINAL_CURRENT = 45.0      # A
    NOMINAL_POWER = 30.0        # kW

    def __init__(self, name: str):
        super().__init__(name)

        self.current = 0.0
        self.power_factor = 0.88
        self.power = 0.0

        self._starting_until = 0.0
        self._cycle_until = 0.0

        self._fault = False
        self._fault_type = None


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


        if self._fault:

            self.current = (
                self.NOMINAL_CURRENT *
                random.uniform(8, 10)
            )

            self.power_factor = random.uniform(
                0.60, 0.70
            )

            self.power = (
                self.NOMINAL_POWER *
                random.uniform(1.2, 1.5)
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
                random.uniform(0.2, 0.5)
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

        if self._fault:
            return

        self._fault = True
        self._fault_type = "overcurrent"


    def stop_fault(self):

        self._fault = False
        self._fault_type = None


    def get_data(self):

        return {
            "name": self.name,
            "state": self.state.value,
            "current": round(self.current, 1),
            "power_factor": round(
                self.power_factor, 2
            ),
            "power_kw": round(
                self.power, 2
            ),
            "fault": self._fault,
            "fault_type": self._fault_type
        }