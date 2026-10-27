import pytest
import dataclasses
from datetime import datetime, date
from src.execution.backtest import BacktestExecutor
from src.models import Signal, OrderStatus


def _signal(action="BUY"):
    return Signal("sys", action, "NSE:NIFTY2410312150CE", "CE", 21500,
                  date(2024, 10, 31), 1, 70.0, 160.0,
                  datetime(2024, 10, 28, 9, 20), "intraday", market_price=100.0)


def test_buy_order_fills_immediately():
    ex = BacktestExecutor()
    oid = ex.place_order(_signal())
    assert ex.get_order_status(oid) == OrderStatus.FILLED


def test_fill_price_includes_slippage():
    ex = BacktestExecutor(slippage_pct=0.001)
    oid = ex.place_order(_signal())
    assert ex._orders[oid].fill_price == pytest.approx(100.1)


def test_brokerage_charged_on_entry():
    ex = BacktestExecutor(brokerage_per_order=20.0)
    ex.place_order(_signal())
    assert ex.total_brokerage == pytest.approx(20.0)


def test_brokerage_charged_on_exit_too():
    ex = BacktestExecutor(brokerage_per_order=20.0)
    ex.place_order(_signal("BUY"))
    ex.place_order(dataclasses.replace(_signal("SELL"), symbol="NSE:NIFTY2410312150CE"))
    assert ex.total_brokerage == pytest.approx(40.0)


def test_open_position_tracked():
    ex = BacktestExecutor()
    ex.place_order(_signal("BUY"))
    assert len(ex.get_positions()) == 1


def test_sell_removes_position():
    ex = BacktestExecutor()
    ex.place_order(_signal("BUY"))
    ex.place_order(_signal("SELL"))
    assert len(ex.get_positions()) == 0
