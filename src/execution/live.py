import uuid
from datetime import datetime
from loguru import logger

from src.execution.base import BaseOrderExecutor
from src.models import Order, OrderStatus, Position, Signal

_FYERS_STATUS_MAP = {1: OrderStatus.PENDING, 2: OrderStatus.FILLED, 5: OrderStatus.CANCELLED, 6: OrderStatus.REJECTED}


class LiveExecutor(BaseOrderExecutor):
    def __init__(self, fyers_client, lot_size: int = 65):
        self._fyers = fyers_client
        self._lot_size = lot_size
        self._orders: dict[str, OrderStatus] = {}
        self._positions: dict[str, Position] = {}

    def place_order(self, signal: Signal) -> str:
        product_type = "INTRADAY" if signal.trade_type == "intraday" else "CNC"
        side = 1 if signal.action == "BUY" else -1
        order_data = {
            "symbol": signal.symbol,
            "qty": signal.quantity * self._lot_size,
            "type": 2,
            "side": side,
            "productType": product_type,
            "limitPrice": 0,
            "stopPrice": 0,
            "disclosedQty": 0,
            "validity": "DAY",
            "offlineOrder": False,
        }
        response = self._fyers.place_order(order_data)
        if response.get("s") != "ok":
            oid = str(uuid.uuid4())
            self._orders[oid] = OrderStatus.REJECTED
            logger.warning(f"Order rejected: {response.get('message')}")
            return oid
        oid = response["id"]
        self._orders[oid] = OrderStatus.PENDING
        return oid

    def cancel_order(self, order_id: str) -> bool:
        response = self._fyers.cancel_order({"id": order_id})
        if response.get("s") == "ok":
            self._orders[order_id] = OrderStatus.CANCELLED
            return True
        return False

    def get_order_status(self, order_id: str) -> OrderStatus:
        cached = self._orders.get(order_id)
        if cached == OrderStatus.REJECTED:
            return OrderStatus.REJECTED
        response = self._fyers.orderbook()
        if response.get("s") == "ok":
            for order in response.get("orderBook", []):
                if order["id"] == order_id:
                    return _FYERS_STATUS_MAP.get(order["status"], OrderStatus.PENDING)
        return cached or OrderStatus.PENDING

    def get_positions(self) -> list:
        return list(self._positions.values())
