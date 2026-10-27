import dataclasses
import math
from datetime import date
from typing import List, Tuple

from src.models import Position, Signal


class RiskManager:
    def __init__(self, config):
        self._config = config

    def evaluate(
        self,
        signal: Signal,
        open_positions: List[Position],
        daily_pnl: float,
        account_capital: float,
    ) -> Tuple[bool, str]:
        daily_loss_limit = self._config.risk.daily_loss_limit_pct * account_capital
        if abs(daily_pnl) >= daily_loss_limit and daily_pnl < 0:
            return False, "daily loss limit reached"

        if len(open_positions) >= self._config.risk.max_open_positions:
            return False, f"max open positions ({self._config.risk.max_open_positions}) reached"

        if self.is_near_expiry(signal.expiry, signal.trade_type):
            return False, f"expiry too close for positional trade ({signal.expiry})"

        return True, "approved"

    def is_near_expiry(self, expiry: date, trade_type: str) -> bool:
        if trade_type != "positional":
            return False
        return (expiry - date.today()).days <= 2

    def calculate_position_size(self, account_capital: float, sl_points: float) -> int:
        risk_amount = account_capital * self._config.risk.max_capital_per_trade_pct
        lot_size = self._config.risk.lot_size
        if sl_points <= 0:
            return 1
        lots = math.floor(risk_amount / (sl_points * lot_size))
        return max(1, lots)

    def apply_defaults(self, signal: Signal, entry_price: float) -> Signal:
        sl_price = entry_price * (1 - self._config.risk.default_sl_pct)
        target_price = entry_price * (1 + self._config.risk.default_target_pct)
        return dataclasses.replace(signal, sl_price=sl_price, target_price=target_price)
