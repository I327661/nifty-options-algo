import pytest
from datetime import datetime, date
from src.models import Candle, Tick, Signal, Position, Order, OrderStatus


def test_candle_is_frozen():
    c = Candle("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20),
               21500.0, 21550.0, 21490.0, 21530.0, 1000, "5m")
    with pytest.raises(Exception):
        c.close = 0.0


def test_signal_has_market_price_default():
    s = Signal("directional", "BUY", "NSE:NIFTY2410223650CE", "CE", 23650,
               date(2024, 10, 22), 1, 80.0, 160.0, datetime(2024, 1, 2, 9, 25), "intraday")
    assert s.market_price == 0.0


def test_position_is_mutable():
    pos = Position("pos_1", "sys", "NSE:NIFTY2410223650CE", "CE", 23650,
                   date(2024, 10, 22), 100.0, 1, 70.0, 160.0,
                   datetime(2024, 1, 2, 9, 20), "intraday")
    pos.current_price = 120.0
    assert pos.current_price == 120.0


def test_order_status_values():
    assert OrderStatus.FILLED.value == "FILLED"
    assert OrderStatus.REJECTED.value == "REJECTED"
    assert OrderStatus.PENDING.value == "PENDING"
    assert OrderStatus.CANCELLED.value == "CANCELLED"
