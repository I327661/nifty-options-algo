from unittest.mock import MagicMock
from datetime import datetime, date
from src.execution.live import LiveExecutor
from src.models import Signal, OrderStatus


def _signal():
    return Signal("sys", "BUY", "NSE:NIFTY2410312150CE", "CE", 21500,
                  date(2024, 10, 31), 1, 70.0, 160.0,
                  datetime(2024, 10, 28, 9, 20), "intraday")


def test_place_order_calls_fyers():
    fyers = MagicMock()
    fyers.place_order.return_value = {"s": "ok", "id": "fid_123"}
    ex = LiveExecutor(fyers)
    oid = ex.place_order(_signal())
    fyers.place_order.assert_called_once()
    assert oid == "fid_123"


def test_rejected_order_status_is_rejected():
    fyers = MagicMock()
    fyers.place_order.return_value = {"s": "error", "message": "Insufficient funds"}
    ex = LiveExecutor(fyers)
    oid = ex.place_order(_signal())
    assert ex.get_order_status(oid) == OrderStatus.REJECTED


def test_order_status_maps_fyers_code_filled():
    fyers = MagicMock()
    fyers.place_order.return_value = {"s": "ok", "id": "oid_1"}
    fyers.orderbook.return_value = {"s": "ok", "orderBook": [{"id": "oid_1", "status": 2}]}
    ex = LiveExecutor(fyers)
    ex._orders["oid_1"] = MagicMock()
    assert ex.get_order_status("oid_1") == OrderStatus.FILLED


def test_order_status_maps_fyers_code_rejected():
    fyers = MagicMock()
    fyers.place_order.return_value = {"s": "ok", "id": "oid_2"}
    fyers.orderbook.return_value = {"s": "ok", "orderBook": [{"id": "oid_2", "status": 6}]}
    ex = LiveExecutor(fyers)
    ex._orders["oid_2"] = MagicMock()
    assert ex.get_order_status("oid_2") == OrderStatus.REJECTED
