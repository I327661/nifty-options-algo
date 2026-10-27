from datetime import datetime, date
from unittest.mock import MagicMock
from src.strategies.scalping import ScalpingStrategy
from src.models import Candle


def _candle(close, ts):
    return Candle("NSE:NIFTY50-INDEX", ts, close - 5, close + 5, close - 8, close, 500, "1m")


def _strategy():
    return ScalpingStrategy("scalp", {
        "sl_pct": 0.25, "target_pct": 0.40, "trade_type": "intraday"
    }, symbol_resolver=MagicMock())


def _resolver():
    r = MagicMock()
    r.get_current_expiry.return_value = date(2024, 1, 2)
    r.get_atm_symbol.return_value = "NSE:NIFTY2401021500CE"
    return r


def _above_vwap_candle(close, volume, ts):
    return Candle("NSE:NIFTY50-INDEX", ts, close-5, close+5, close-8, close, volume, "5m")


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


def test_max_3_entries_per_day():
    """Only 3 signals on same day even when VWAP conditions fire 5 times."""
    s = ScalpingStrategy("scalp", {"trade_type": "intraday"}, _resolver())

    # Seed: low price candle anchors VWAP at ~20000
    s.on_candle(_above_vwap_candle(20000, 100, datetime(2024, 1, 2, 9, 20)))
    s.generate_signal()

    # 5 candles far above VWAP with rising volume — only 3 should produce signals
    signals = []
    for i in range(5):
        ts = datetime(2024, 1, 2, 9, 25 + i * 5)
        s.on_candle(_above_vwap_candle(22000 + i * 10, 1000 + i * 100, ts))
        sig = s.generate_signal()
        if sig is not None:
            signals.append(sig)

    assert len(signals) == 3


def test_daily_cap_resets_on_new_day_scalping():
    """After hitting the 3-entry cap on day 1, signals resume on day 2."""
    s = ScalpingStrategy("scalp", {"trade_type": "intraday"}, _resolver())

    # Day 1: seed + 3 signals
    s.on_candle(_above_vwap_candle(20000, 100, datetime(2024, 1, 2, 9, 20)))
    s.generate_signal()
    for i in range(3):
        s.on_candle(_above_vwap_candle(22000 + i * 10, 1000 + i * 100, datetime(2024, 1, 2, 9, 25 + i * 5)))
        s.generate_signal()
    assert s._trades_today == 3

    # Day 2: new seed, then a signal-worthy candle
    s.on_candle(_above_vwap_candle(20000, 100, datetime(2024, 1, 3, 9, 20)))
    s.generate_signal()
    s.on_candle(_above_vwap_candle(22000, 1000, datetime(2024, 1, 3, 9, 25)))
    sig = s.generate_signal()

    assert s._trades_today == 1
    assert sig is not None


def test_reset_clears_trade_counter_scalping():
    s = _strategy()
    s._trades_today = 2
    s.reset()
    assert s._trades_today == 0
