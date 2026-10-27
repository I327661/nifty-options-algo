from datetime import datetime
from typing import Optional

from src.models import Candle, Tick


class CandleBuilder:
    def __init__(self, symbol: str, timeframe_minutes: int):
        self._symbol = symbol
        self._timeframe_minutes = timeframe_minutes
        self._window_start: Optional[datetime] = None
        self._open: float = 0.0
        self._high: float = 0.0
        self._low: float = float("inf")
        self._last_close: float = 0.0
        self._volume: int = 0

    def _floor_to_window(self, ts: datetime) -> datetime:
        total_minutes = ts.hour * 60 + ts.minute
        floored = (total_minutes // self._timeframe_minutes) * self._timeframe_minutes
        return ts.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)

    def on_tick(self, tick: Tick) -> Optional[Candle]:
        window = self._floor_to_window(tick.timestamp)
        completed = None

        if self._window_start is None:
            self._window_start = window
            self._open = tick.ltp
            self._high = tick.ltp
            self._low = tick.ltp
            self._last_close = tick.ltp
            self._volume = tick.volume
        elif window != self._window_start:
            timeframe_label = f"{self._timeframe_minutes}m"
            completed = Candle(
                symbol=self._symbol,
                timestamp=self._window_start,
                open=self._open,
                high=self._high,
                low=self._low,
                close=self._last_close,
                volume=self._volume,
                timeframe=timeframe_label,
            )
            self._window_start = window
            self._open = tick.ltp
            self._high = tick.ltp
            self._low = tick.ltp
            self._last_close = tick.ltp
            self._volume = tick.volume
        else:
            self._high = max(self._high, tick.ltp)
            self._low = min(self._low, tick.ltp)
            self._last_close = tick.ltp
            self._volume += tick.volume

        return completed

    def get_current_state(self) -> dict:
        return {
            "window_start": self._window_start,
            "open": self._open,
            "high": self._high,
            "low": self._low,
            "last_close": self._last_close,
            "volume": self._volume,
        }

    def restore_state(self, state: dict) -> None:
        self._window_start = state["window_start"]
        self._open = state["open"]
        self._high = state["high"]
        self._low = state["low"]
        self._last_close = state["last_close"]
        self._volume = state["volume"]
