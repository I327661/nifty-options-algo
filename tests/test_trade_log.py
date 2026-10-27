import pytest
from datetime import datetime, date
from src.portfolio.trade_log import TradeLog
from src.models import Position


def _pos(pid="p1"):
    return Position(pid, "sys", "NSE:NIFTY2410312150CE", "CE", 21500,
                    date(2024, 10, 31), 100.0, 1, 70.0, 160.0,
                    datetime(2024, 10, 28, 9, 20), "intraday")


def test_log_and_retrieve_trade(tmp_path):
    log = TradeLog(str(tmp_path / "t.db"))
    log.log_trade_closed(_pos(), 150.0, "target", datetime(2024, 10, 28, 10, 0))
    trades = log.get_trades(date(2024, 10, 28))
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "target"
    assert trades[0]["pnl"] == pytest.approx((150.0 - 100.0) * 65 * 1)


def test_daily_summary_wins_losses(tmp_path):
    log = TradeLog(str(tmp_path / "t.db"))
    log.log_trade_closed(_pos("p1"), 150.0, "target", datetime(2024, 10, 28, 10, 0))
    log.log_trade_closed(_pos("p2"), 70.0, "SL", datetime(2024, 10, 28, 10, 5))
    s = log.get_daily_summary(date(2024, 10, 28))
    assert s["trades"] == 2
    assert s["wins"] == 1
    assert s["losses"] == 1
    assert s["net_pnl"] == pytest.approx((150.0 - 100.0) * 65 + (70.0 - 100.0) * 65)


def test_get_trades_filters_by_date(tmp_path):
    log = TradeLog(str(tmp_path / "t.db"))
    log.log_trade_closed(_pos("p1"), 150.0, "target", datetime(2024, 10, 27, 10, 0))
    log.log_trade_closed(_pos("p2"), 150.0, "target", datetime(2024, 10, 28, 10, 0))
    assert len(log.get_trades(date(2024, 10, 28))) == 1
