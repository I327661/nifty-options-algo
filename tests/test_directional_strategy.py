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


def test_bullish_crossover_generates_ce_signal():
    """EMA9 crossing above EMA21 with RSI < 70 must produce a CE signal."""
    resolver = MagicMock()
    resolver.get_current_expiry.return_value = date(2024, 10, 31)
    resolver.get_atm_symbol.return_value = "NSE:NIFTY2410312150CE"
    s = DirectionalStrategy("dir", {
        "ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "trade_type": "intraday"
    }, symbol_resolver=resolver)

    # 30 declining candles: fast EMA falls faster than slow → fast < slow
    decline = [22000 - i * 60 for i in range(30)]
    # 30 sharply rising candles: fast EMA recovers faster → bullish crossover
    rise = [20260 + i * 200 for i in range(30)]

    signals = []
    base_dt = datetime(2024, 10, 28, 9, 20)
    for price in decline + rise:
        s.on_candle(Candle("NSE:NIFTY50-INDEX", base_dt, price - 5, price + 5, price - 10, price, 1000, "5m"))
        sig = s.generate_signal()
        if sig is not None:
            signals.append(sig)

    ce_signals = [sig for sig in signals if sig.option_type == "CE"]
    assert len(ce_signals) >= 1, "Expected at least one CE signal from bullish EMA crossover"
    assert ce_signals[0].action == "BUY"

