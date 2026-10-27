from typing import Optional

from src.models import Candle, Signal
from src.strategies.base import BaseStrategy


class SystematicStrategy(BaseStrategy):
    def __init__(self, name: str, parameters: dict, symbol_resolver):
        super().__init__(name, parameters)
        self.symbol_resolver = symbol_resolver
        self._pending_signal: Optional[Signal] = None

    def on_candle(self, candle: Candle) -> None:
        entry_days = self.parameters.get("entry_days", [])
        entry_time = self.parameters.get("entry_time", "09:20")
        option_type = self.parameters.get("option_type", "CE")

        day_name = candle.timestamp.strftime("%A")
        candle_time = candle.timestamp.strftime("%H:%M")

        if day_name not in entry_days or candle_time != entry_time:
            return

        try:
            expiry = self.symbol_resolver.get_current_expiry(as_of=candle.timestamp.date())
            symbol = self.symbol_resolver.get_atm_symbol(candle.close, option_type, expiry)
        except Exception:
            return

        self._pending_signal = Signal(
            strategy=self.name,
            action="BUY",
            symbol=symbol,
            option_type=option_type,
            strike=0,
            expiry=expiry,
            quantity=1,
            sl_price=0.0,
            target_price=0.0,
            timestamp=candle.timestamp,
            trade_type=self.parameters.get("trade_type", "intraday"),
        )

    def generate_signal(self) -> Optional[Signal]:
        signal = self._pending_signal
        self._pending_signal = None
        return signal

    def reset(self) -> None:
        self._pending_signal = None
