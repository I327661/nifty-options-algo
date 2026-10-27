from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str


@dataclass(frozen=True)
class Tick:
    symbol: str
    timestamp: datetime
    ltp: float
    volume: int


@dataclass(frozen=True)
class Signal:
    strategy: str
    action: str
    symbol: str
    option_type: str
    strike: int
    expiry: date
    quantity: int
    sl_price: float
    target_price: float
    timestamp: datetime
    trade_type: str
    market_price: float = 0.0


@dataclass
class Position:
    position_id: str
    strategy: str
    symbol: str
    option_type: str
    strike: int
    expiry: date
    entry_price: float
    quantity: int
    sl_price: float
    target_price: float
    entry_time: datetime
    trade_type: str
    current_price: float = 0.0


@dataclass
class Order:
    order_id: str
    symbol: str
    action: str
    quantity: int
    order_type: str
    price: float
    status: OrderStatus
    timestamp: datetime
    fill_price: float = 0.0
