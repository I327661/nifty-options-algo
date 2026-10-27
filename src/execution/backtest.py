import uuid
from datetime import datetime

from src.execution.base import BaseOrderExecutor
from src.models import Order, OrderStatus, Position, Signal


class BacktestExecutor(BaseOrderExecutor):
    def __init__(self, slippage_pct: float = 0.0005, brokerage_per_order: float = 20.0, lot_size: int = 65):
        self._slippage_pct = slippage_pct
        self._brokerage_per_order = brokerage_per_order
        self._lot_size = lot_size
        self._orders: dict[str, Order] = {}
        self._positions: dict[str, Position] = {}
        self.total_brokerage: float = 0.0

    def place_order(self, signal: Signal) -> str:
        order_id = str(uuid.uuid4())
        if signal.action == "BUY":
            fill_price = signal.market_price * (1 + self._slippage_pct)
        else:
            fill_price = signal.market_price * (1 - self._slippage_pct)

        order = Order(
            order_id=order_id,
            symbol=signal.symbol,
            action=signal.action,
            quantity=signal.quantity,
            order_type="MARKET",
            price=signal.market_price,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
            fill_price=fill_price,
        )
        self._orders[order_id] = order
        self.total_brokerage += self._brokerage_per_order

        if signal.action == "BUY":
            pos = Position(
                position_id=order_id,
                strategy=signal.strategy,
                symbol=signal.symbol,
                option_type=signal.option_type,
                strike=signal.strike,
                expiry=signal.expiry,
                entry_price=fill_price,
                quantity=signal.quantity,
                sl_price=signal.sl_price,
                target_price=signal.target_price,
                entry_time=order.timestamp,
                trade_type=signal.trade_type,
            )
            self._positions[signal.symbol] = pos
        elif signal.action == "SELL":
            self._positions.pop(signal.symbol, None)

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id] = Order(
                **{**vars(self._orders[order_id]), "status": OrderStatus.CANCELLED}
            )
            return True
        return False

    def get_order_status(self, order_id: str) -> OrderStatus:
        return self._orders[order_id].status

    def get_positions(self) -> list:
        return list(self._positions.values())
