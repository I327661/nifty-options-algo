import dataclasses
from datetime import datetime
from typing import Optional

from src.models import Position
from src.portfolio.trade_log import TradeLog


class PortfolioManager:
    def __init__(self, trade_log: TradeLog, lot_size: int = 65, illiquid_threshold: float = 0.0):
        self._trade_log = trade_log
        self._lot_size = lot_size
        self._illiquid_threshold = illiquid_threshold
        self._open: dict[str, Position] = {}
        self._closed_today: list[tuple[Position, float]] = []

    def open_position(self, position: Position) -> None:
        self._open[position.position_id] = position

    def close_position(self, position_id: str, exit_price: float, exit_reason: str) -> None:
        position = self._open.pop(position_id)
        self._closed_today.append((position, exit_price))
        self._trade_log.log_trade_closed(position, exit_price, exit_reason, datetime.now())

    def update_prices(self, symbol: str, current_price: float) -> list:
        triggered = []
        to_close = []
        for pid, pos in self._open.items():
            if pos.symbol != symbol:
                continue
            self._open[pid] = dataclasses.replace(pos, current_price=current_price)
            if current_price >= pos.target_price:
                to_close.append((pid, current_price, "target"))
            elif current_price <= pos.sl_price:
                to_close.append((pid, current_price, "SL"))
            elif self._illiquid_threshold > 0 and current_price < self._illiquid_threshold:
                to_close.append((pid, current_price, "illiquid"))
        for pid, price, reason in to_close:
            triggered.append(self._open[pid])
            self.close_position(pid, price, reason)
        return triggered

    def get_open_positions(self) -> list:
        return list(self._open.values())

    def get_intraday_positions(self) -> list:
        return [p for p in self._open.values() if p.trade_type == "intraday"]

    def get_daily_pnl(self) -> float:
        return sum(
            (exit_price - pos.entry_price) * pos.quantity * self._lot_size
            for pos, exit_price in self._closed_today
        )
