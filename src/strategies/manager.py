from typing import List, Optional

from src.models import Candle, Signal, Tick
from src.strategies.base import BaseStrategy


class StrategyManager:
    def __init__(self, strategies: List[BaseStrategy]):
        self._strategies = strategies

    def on_candle(self, candle: Candle) -> None:
        for strategy in self._strategies:
            strategy.on_candle(candle)

    def on_tick(self, tick: Tick) -> None:
        for strategy in self._strategies:
            strategy.on_tick(tick)

    def collect_signals(self) -> List[Signal]:
        signals = []
        for strategy in self._strategies:
            signal = strategy.generate_signal()
            if signal is not None:
                signals.append(signal)
        return signals

    def reset_all(self) -> None:
        for strategy in self._strategies:
            strategy.reset()
