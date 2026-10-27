from unittest.mock import MagicMock
from src.strategies.manager import StrategyManager
from src.models import Candle, Signal
from datetime import datetime


def test_routes_candle_to_all_strategies():
    s1, s2 = MagicMock(), MagicMock()
    s1.generate_signal.return_value = None
    s2.generate_signal.return_value = None
    mgr = StrategyManager([s1, s2])
    c = Candle("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20),
               21500.0, 21550.0, 21490.0, 21530.0, 1000, "5m")
    mgr.on_candle(c)
    s1.on_candle.assert_called_once_with(c)
    s2.on_candle.assert_called_once_with(c)


def test_collect_signals_filters_none():
    s1, s2 = MagicMock(), MagicMock()
    sig = MagicMock(spec=Signal)
    s1.generate_signal.return_value = sig
    s2.generate_signal.return_value = None
    mgr = StrategyManager([s1, s2])
    assert mgr.collect_signals() == [sig]


def test_reset_all_calls_reset_on_each():
    s1, s2 = MagicMock(), MagicMock()
    mgr = StrategyManager([s1, s2])
    mgr.reset_all()
    s1.reset.assert_called_once()
    s2.reset.assert_called_once()
