import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock
from src.risk.manager import RiskManager
from src.models import Signal, Position


def _config():
    c = MagicMock()
    c.risk.lot_size = 65
    c.risk.max_capital_per_trade_pct = 0.02
    c.risk.daily_loss_limit_pct = 0.01
    c.risk.max_open_positions = 3
    c.risk.default_sl_pct = 0.30
    c.risk.default_target_pct = 0.60
    return c


def _signal(trade_type="intraday", expiry=None):
    return Signal("sys", "BUY", "NSE:NIFTY2410312150CE", "CE", 21500,
                  expiry or date(2024, 10, 31), 1, 0.0, 0.0,
                  datetime(2024, 10, 28, 9, 20), trade_type)


def test_rejects_on_daily_loss_limit():
    rm = RiskManager(_config())
    approved, reason = rm.evaluate(_signal(), [], daily_pnl=-1100.0, account_capital=100000.0)
    assert not approved
    assert "daily loss" in reason.lower()


def test_existing_positions_stay_open_when_limit_hit():
    rm = RiskManager(_config())
    approved, reason = rm.evaluate(_signal(), [], daily_pnl=-1100.0, account_capital=100000.0)
    assert not approved


def test_rejects_on_max_positions():
    rm = RiskManager(_config())
    positions = [MagicMock() for _ in range(3)]
    approved, reason = rm.evaluate(_signal(), positions, 0.0, 100000.0)
    assert not approved
    assert "position" in reason.lower()


def test_rejects_positional_near_expiry():
    rm = RiskManager(_config())
    expiry = date.today() + timedelta(days=1)
    approved, reason = rm.evaluate(_signal("positional", expiry), [], 0.0, 100000.0)
    assert not approved
    assert "expiry" in reason.lower()


def test_rejects_positional_on_expiry_day():
    rm = RiskManager(_config())
    approved, reason = rm.evaluate(_signal("positional", date.today()), [], 0.0, 100000.0)
    assert not approved


def test_approves_intraday_near_expiry():
    rm = RiskManager(_config())
    expiry = date.today() + timedelta(days=1)
    approved, _ = rm.evaluate(_signal("intraday", expiry), [], 0.0, 100000.0)
    assert approved


def test_position_sizing_floors_to_integer():
    rm = RiskManager(_config())
    assert rm.calculate_position_size(100000.0, 30.0) == 1


def test_position_sizing_minimum_one_lot():
    rm = RiskManager(_config())
    assert rm.calculate_position_size(100.0, 1000.0) == 1


def test_apply_defaults_sets_sl_and_target():
    rm = RiskManager(_config())
    sig = _signal()
    updated = rm.apply_defaults(sig, entry_price=100.0)
    assert updated.sl_price == pytest.approx(70.0)
    assert updated.target_price == pytest.approx(160.0)
