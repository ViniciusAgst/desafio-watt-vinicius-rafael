from abc import ABC, abstractmethod
from enum import Enum

class Device(ABC):

    def __init__(self, name: str):
        self.name = name
        self.state = State.STOPPED

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def start_fault(self) -> None:
        pass

    @abstractmethod
    def stop_fault(self) -> None:
        pass

    @abstractmethod
    def get_data(self) -> dict:
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.name}', state='{self.state}')"


class State(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAULT = "fault"
    MAINTENANCE = "maintenance"