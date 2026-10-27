from unittest.mock import MagicMock
from datetime import datetime, date
import dataclasses
from src.engine import Engine
from src.models import Candle, Signal


def _candle():
    return Candle("NSE:NIFTY50-INDEX", datetime(2024, 10, 28, 9, 25),
                  21500.0, 21550.0, 21490.0, 21530.0, 1000, "5m")


def _sig():
    return Signal("sys", "BUY", "NSE:NIFTY2410312150CE", "CE", 21500,
                  date(2024, 10, 31), 1, 0.0, 0.0,
                  datetime(2024, 10, 28, 9, 25), "intraday")


def _engine(sig, risk_approved=True):
    sm, rm, ex, pm = MagicMock(), MagicMock(), MagicMock(), MagicMock()
    sm.collect_signals.return_value = [sig] if sig else []
    rm.evaluate.return_value = (risk_approved, "approved" if risk_approved else "rejected")
    rm.apply_defaults.return_value = sig
    pm.get_open_positions.return_value = []
    pm.get_daily_pnl.return_value = 0.0
    pm.update_prices.return_value = []
    cfg = MagicMock()
    cfg.risk.account_capital = 100000.0
    return Engine(sm, rm, ex, pm, cfg), ex, pm


def test_approved_signal_reaches_executor():
    engine, ex, _ = _engine(_sig(), risk_approved=True)
    engine.on_candle(_candle())
    ex.place_order.assert_called_once()


def test_market_price_set_on_signal_before_executor():
    engine, ex, _ = _engine(_sig(), risk_approved=True)
    engine.on_candle(_candle())
    placed_signal = ex.place_order.call_args[0][0]
    assert placed_signal.market_price == 21530.0


def test_rejected_signal_skips_executor():
    engine, ex, _ = _engine(_sig(), risk_approved=False)
    engine.on_candle(_candle())
    ex.place_order.assert_not_called()


def test_sl_trigger_from_tick_places_sell():
    engine, ex, pm = _engine(None)
    from src.models import Position, Tick
    triggered_pos = Position("p1", "sys", "NSE:NIFTY2410312150CE", "CE", 21500,
                             date(2024, 10, 31), 100.0, 1, 70.0, 160.0,
                             datetime(2024, 10, 28, 9, 20), "intraday", current_price=69.0)
    pm.update_prices.return_value = [triggered_pos]
    tick = Tick("NSE:NIFTY2410312150CE", datetime(2024, 10, 28, 9, 25), 69.0, 100)
    engine.on_tick(tick)
    ex.place_order.assert_called_once()
    sell_signal = ex.place_order.call_args[0][0]
    assert sell_signal.action == "SELL"
