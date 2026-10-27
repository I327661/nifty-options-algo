from datetime import datetime, time
from typing import Optional

from src.models import Candle, Signal
from src.strategies.base import BaseStrategy

MORNING_START = time(9, 20)
MORNING_END = time(11, 30)
AFTERNOON_START = time(13, 30)
AFTERNOON_END = time(15, 0)


class ScalpingStrategy(BaseStrategy):
    def __init__(self, name: str, parameters: dict, symbol_resolver):
        super().__init__(name, parameters)
        self.symbol_resolver = symbol_resolver
        self._candles: list[Candle] = []
        self._pending_signal: Optional[Signal] = None
        self._cum_tp_vol: float = 0.0
        self._cum_vol: int = 0
        self._last_day = None

    def _is_in_active_window(self, ts: datetime) -> bool:
        t = ts.time()
        morning = MORNING_START <= t <= MORNING_END
        afternoon = AFTERNOON_START <= t <= AFTERNOON_END
        return morning or afternoon

    def on_candle(self, candle: Candle) -> None:
        if not self._is_in_active_window(candle.timestamp):
            return

        if self._last_day != candle.timestamp.date():
            self._cum_tp_vol = 0.0
            self._cum_vol = 0
            self._candles = []
            self._last_day = candle.timestamp.date()

        self._candles.append(candle)
        typical_price = (candle.high + candle.low + candle.close) / 3
        self._cum_tp_vol += typical_price * candle.volume
        self._cum_vol += candle.volume

        if self._cum_vol == 0 or len(self._candles) < 2:
            return

        vwap = self._cum_tp_vol / self._cum_vol
        prev_candle = self._candles[-2]
        price_above_vwap = candle.close > vwap * 1.001
        price_below_vwap = candle.close < vwap * 0.999
        volume_rising = candle.volume > prev_candle.volume

        if price_above_vwap and volume_rising:
            option_type = "CE"
        elif price_below_vwap and volume_rising:
            option_type = "PE"
        else:
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
        self._candles = []
        self._pending_signal = None
        self._cum_tp_vol = 0.0
        self._cum_vol = 0
        self._last_day = None
