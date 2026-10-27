from datetime import datetime, date
from unittest.mock import MagicMock
from src.strategies.directional import DirectionalStrategy
from src.models import Candle


def _candle(close, ts=None):
    ts = ts or datetime(2024, 1, 2, 9, 20)
    return Candle("NSE:NIFTY50-INDEX", ts, close - 10, close + 10, close - 15, close, 1000, "5m")


def _strategy():
    return DirectionalStrategy("dir", {
        "ema_fast": 9, "ema_slow": 21, "rsi_period": 14,
        "sl_pct": 0.30, "target_pct": 0.60, "trade_type": "intraday"
    }, symbol_resolver=MagicMock())


def test_no_signal_with_insufficient_data():
    s = _strategy()
    s.on_candle(_candle(21500.0))
    assert s.generate_signal() is None


def test_signal_cleared_after_generate():
    s = _strategy()
    s._pending_signal = MagicMock()
    s.generate_signal()
    assert s.generate_signal() is None


def test_reset_clears_candle_history():
    s = _strategy()
    for i in range(5):
        s.on_candle(_candle(21500.0 + i))
    s.reset()
    assert len(s._candles) == 0
    assert s._pending_signal is None
