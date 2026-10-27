from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.models import Candle, Signal
from src.strategies.base import BaseStrategy


class DirectionalStrategy(BaseStrategy):
    def __init__(self, name: str, parameters: dict, symbol_resolver):
        super().__init__(name, parameters)
        self.symbol_resolver = symbol_resolver
        self._candles: list[Candle] = []
        self._pending_signal: Optional[Signal] = None
        self._trades_today: int = 0
        self._last_day = None

    def on_candle(self, candle: Candle) -> None:
        self._candles.append(candle)
        self._pending_signal = None

        candle_day = candle.timestamp.date()
        if self._last_day != candle_day:
            self._trades_today = 0
            self._last_day = candle_day

        if self._trades_today >= 3:
            return

        ema_fast = self.parameters.get("ema_fast", 9)
        ema_slow = self.parameters.get("ema_slow", 21)
        rsi_period = self.parameters.get("rsi_period", 14)

        min_required = ema_slow + rsi_period + 2
        if len(self._candles) < min_required:
            return

        closes = np.array([c.close for c in self._candles], dtype=float)

        try:
            import talib
            ema_fast_arr = talib.EMA(closes, timeperiod=ema_fast)
            ema_slow_arr = talib.EMA(closes, timeperiod=ema_slow)
            rsi_arr = talib.RSI(closes, timeperiod=rsi_period)
        except Exception:
            return

        if len(ema_fast_arr) < 2 or len(ema_slow_arr) < 2:
            return

        prev_fast, curr_fast = ema_fast_arr[-2], ema_fast_arr[-1]
        prev_slow, curr_slow = ema_slow_arr[-2], ema_slow_arr[-1]
        rsi = rsi_arr[-1]

        if any(np.isnan(v) for v in [prev_fast, prev_slow, curr_fast, curr_slow, rsi]):
            return

        bullish_crossover = (prev_fast <= prev_slow) and (curr_fast > curr_slow)
        bearish_crossover = (prev_fast >= prev_slow) and (curr_fast < curr_slow)

        if bullish_crossover and rsi < 70:
            option_type = "CE"
        elif bearish_crossover and rsi > 30:
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
        self._trades_today += 1

    def generate_signal(self) -> Optional[Signal]:
        signal = self._pending_signal
        self._pending_signal = None
        return signal

    def reset(self) -> None:
        self._candles = []
        self._pending_signal = None
        self._trades_today = 0
        self._last_day = None
