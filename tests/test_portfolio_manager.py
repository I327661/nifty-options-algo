import pytest
from datetime import datetime, date
from src.portfolio.manager import PortfolioManager
from src.portfolio.trade_log import TradeLog
from src.models import Position


def _pos(pid="p1", sl=70.0, target=160.0, trade_type="intraday"):
    return Position(pid, "sys", "NSE:NIFTY2410312150CE", "CE", 21500,
                    date(2024, 10, 31), 100.0, 1, sl, target,
                    datetime(2024, 10, 28, 9, 20), trade_type)


def test_open_and_retrieve(tmp_path):
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")))
    pm.open_position(_pos())
    assert len(pm.get_open_positions()) == 1


def test_target_triggers_exit(tmp_path):
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")))
    pm.open_position(_pos(target=160.0))
    triggered = pm.update_prices("NSE:NIFTY2410312150CE", 161.0)
    assert len(triggered) == 1
    assert len(pm.get_open_positions()) == 0


def test_sl_triggers_exit(tmp_path):
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")))
    pm.open_position(_pos(sl=70.0))
    triggered = pm.update_prices("NSE:NIFTY2410312150CE", 69.0)
    assert len(triggered) == 1


def test_daily_pnl_after_close(tmp_path):
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")))
    pm.open_position(_pos())
    pm.close_position("p1", 150.0, "target")
    assert pm.get_daily_pnl() == pytest.approx((150.0 - 100.0) * 65)


def test_get_intraday_positions_filters(tmp_path):
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")))
    pm.open_position(_pos("p1", trade_type="intraday"))
    pm.open_position(_pos("p2", trade_type="positional"))
    assert len(pm.get_intraday_positions()) == 1


def test_illiquid_premium_triggers_exit(tmp_path):
    """Position with premium below illiquid threshold must be auto-closed."""
    pm = PortfolioManager(TradeLog(str(tmp_path / "t.db")), illiquid_threshold=5.0)
    pm.open_position(_pos(sl=2.0, target=200.0))  # SL and target far away
    triggered = pm.update_prices("NSE:NIFTY2410312150CE", 4.0)  # below threshold
    assert len(triggered) == 1
    assert len(pm.get_open_positions()) == 0
