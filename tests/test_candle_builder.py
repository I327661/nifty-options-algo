from datetime import datetime
from src.data.candle_builder import CandleBuilder
from src.models import Tick


def test_returns_none_within_window():
    b = CandleBuilder("NSE:NIFTY50-INDEX", 1)
    t = Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 5), 21500.0, 100)
    assert b.on_tick(t) is None


def test_emits_candle_on_new_window():
    b = CandleBuilder("NSE:NIFTY50-INDEX", 1)
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 5), 21500.0, 100))
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 30), 21520.0, 200))
    candle = b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 21, 5), 21510.0, 150))
    assert candle is not None
    assert candle.open == 21500.0
    assert candle.high == 21520.0
    assert candle.low == 21500.0
    assert candle.close == 21520.0
    assert candle.timeframe == "1m"


def test_high_low_tracked_correctly():
    b = CandleBuilder("NSE:NIFTY50-INDEX", 5)
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 0), 21500.0, 100))
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 30), 21550.0, 100))
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 21, 0), 21480.0, 100))
    candle = b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 25, 0), 21490.0, 100))
    assert candle.high == 21550.0
    assert candle.low == 21480.0


def test_state_preserved_after_restore():
    b = CandleBuilder("NSE:NIFTY50-INDEX", 5)
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 20, 0), 21500.0, 100))
    b.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 21, 0), 21550.0, 100))
    state = b.get_current_state()
    b2 = CandleBuilder("NSE:NIFTY50-INDEX", 5)
    b2.restore_state(state)
    candle = b2.on_tick(Tick("NSE:NIFTY50-INDEX", datetime(2024, 1, 2, 9, 25, 0), 21490.0, 100))
    assert candle is not None
    assert candle.open == 21500.0
