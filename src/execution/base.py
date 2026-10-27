from abc import ABC, abstractmethod

from src.models import OrderStatus, Position, Signal


class BaseOrderExecutor(ABC):
    @abstractmethod
    def place_order(self, signal: Signal) -> str: ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: ...

    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus: ...

    @abstractmethod
    def get_positions(self) -> list: ...
