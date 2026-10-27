from abc import ABC, abstractmethod
from typing import Optional

from src.models import Candle, Signal, Tick


class BaseStrategy(ABC):
    def __init__(self, name: str, parameters: dict):
        self.name = name
        self.parameters = parameters

    @abstractmethod
    def on_candle(self, candle: Candle) -> None:
        pass

    @abstractmethod
    def generate_signal(self) -> Optional[Signal]:
        pass

    def on_tick(self, tick: Tick) -> None:
        pass

    def reset(self) -> None:
        pass
