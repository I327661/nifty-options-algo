import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from loguru import logger

from src.data.candle_builder import CandleBuilder
from src.models import Candle, Tick

TIMEFRAMES = [1, 5, 15]


class LiveFeed:
    def __init__(
        self,
        fyers_client,
        symbols: List[str],
        on_candle: Callable[[Candle], None],
        on_tick: Callable[[Tick], None],
    ):
        self._fyers = fyers_client
        self._symbols = list(symbols)
        self._on_candle = on_candle
        self._on_tick = on_tick
        self._reconnect_attempts = 0
        self._ws = None

        self._candle_builders: Dict[Tuple[str, int], CandleBuilder] = {}
        for symbol in symbols:
            for tf in TIMEFRAMES:
                self._candle_builders[(symbol, tf)] = CandleBuilder(symbol, tf)

    def _on_message(self, message: dict) -> None:
        if message.get("type") != "sf":
            return
        symbol = message.get("symbol", "")
        ltp = float(message.get("ltp", 0))
        volume = int(message.get("vol_traded_today", 0))
        tt = message.get("tt", 0)
        timestamp = datetime.fromtimestamp(tt)

        tick = Tick(symbol=symbol, timestamp=timestamp, ltp=ltp, volume=volume)
        self._on_tick(tick)

        if symbol not in self._symbols:
            self._symbols.append(symbol)
            for tf in TIMEFRAMES:
                if (symbol, tf) not in self._candle_builders:
                    self._candle_builders[(symbol, tf)] = CandleBuilder(symbol, tf)

        for tf in TIMEFRAMES:
            key = (symbol, tf)
            if key in self._candle_builders:
                candle = self._candle_builders[key].on_tick(tick)
                if candle is not None:
                    self._on_candle(candle)

    def _on_close(self, reason: str) -> None:
        self._reconnect_attempts += 1
        delay = min(2 ** self._reconnect_attempts, 64)
        logger.warning(f"WebSocket closed: {reason}. Reconnecting in {delay}s (attempt {self._reconnect_attempts})")
        timer = threading.Timer(delay, self.start)
        timer.daemon = True
        timer.start()

    def subscribe(self, symbol: str) -> None:
        if symbol not in self._symbols:
            self._symbols.append(symbol)
            for tf in TIMEFRAMES:
                self._candle_builders[(symbol, tf)] = CandleBuilder(symbol, tf)

    def start(self) -> None:
        try:
            data_type = "SymbolUpdate"
            symbols = self._symbols
            self._fyers.websocket(
                symbol=symbols,
                data_type=data_type,
                run_background=False,
                on_message=self._on_message,
                on_close=self._on_close,
            )
        except Exception as e:
            logger.error(f"WebSocket start failed: {e}")
            self._on_close(str(e))

    def stop(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
