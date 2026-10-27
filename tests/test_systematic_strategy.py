from datetime import datetime, date
from unittest.mock import MagicMock
from src.strategies.systematic import SystematicStrategy
from src.models import Candle


def test_generates_signal_on_correct_day_and_time():
    s = SystematicStrategy("sys", {
        "entry_days": ["Monday"], "entry_time": "09:20",
        "option_type": "CE", "trade_type": "intraday", "sl_pct": 0.50, "target_pct": 1.0
    }, symbol_resolver=MagicMock())
    s.symbol_resolver.get_current_expiry.return_value = date(2024, 10, 28)
    s.symbol_resolver.get_atm_symbol.return_value = "NSE:NIFTY2410282150CE"
    candle = Candle("NSE:NIFTY50-INDEX", datetime(2024, 10, 28, 9, 20, 0),
                    21500.0, 21550.0, 21490.0, 21530.0, 1000, "1m")
    s.on_candle(candle)
    sig = s.generate_signal()
    assert sig is not None
    assert sig.option_type == "CE"


def test_no_signal_on_wrong_day():
    s = SystematicStrategy("sys", {
        "entry_days": ["Monday"], "entry_time": "09:20",
        "option_type": "CE", "trade_type": "intraday", "sl_pct": 0.50, "target_pct": 1.0
    }, symbol_resolver=MagicMock())
    candle = Candle("NSE:NIFTY50-INDEX", datetime(2024, 10, 29, 9, 20, 0),
                    21500.0, 21550.0, 21490.0, 21530.0, 1000, "1m")
    s.on_candle(candle)
    assert s.generate_signal() is None


def test_no_signal_on_wrong_time():
    s = SystematicStrategy("sys", {
        "entry_days": ["Monday"], "entry_time": "09:20",
        "option_type": "CE", "trade_type": "intraday", "sl_pct": 0.50, "target_pct": 1.0
    }, symbol_resolver=MagicMock())
    candle = Candle("NSE:NIFTY50-INDEX", datetime(2024, 10, 28, 9, 25, 0),
                    21500.0, 21550.0, 21490.0, 21530.0, 1000, "1m")
    s.on_candle(candle)
    assert s.generate_signal() is None
