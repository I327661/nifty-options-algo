from datetime import datetime
from unittest.mock import MagicMock
from src.strategies.scalping import ScalpingStrategy
from src.models import Candle


def _candle(close, ts):
    return Candle("NSE:NIFTY50-INDEX", ts, close - 5, close + 5, close - 8, close, 500, "1m")


def _strategy():
    return ScalpingStrategy("scalp", {
        "sl_pct": 0.25, "target_pct": 0.40, "trade_type": "intraday"
    }, symbol_resolver=MagicMock())


def test_active_window_morning():
    assert _strategy()._is_in_active_window(datetime(2024, 1, 2, 10, 0, 0)) is True


def test_active_window_afternoon():
    assert _strategy()._is_in_active_window(datetime(2024, 1, 2, 14, 0, 0)) is True


def test_inactive_window_midday():
    assert _strategy()._is_in_active_window(datetime(2024, 1, 2, 12, 0, 0)) is False


def test_inactive_window_before_open():
    assert _strategy()._is_in_active_window(datetime(2024, 1, 2, 9, 0, 0)) is False


def test_no_signal_outside_active_window():
    s = _strategy()
    s.on_candle(_candle(21500.0, datetime(2024, 1, 2, 12, 0, 0)))
    assert s.generate_signal() is None


def test_no_signal_on_flat_price():
    s = _strategy()
    for i in range(10):
        s.on_candle(_candle(21500.0, datetime(2024, 1, 2, 9, 20 + i, 0)))
    assert s.generate_signal() is None
