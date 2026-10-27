import dataclasses
from datetime import datetime
from loguru import logger

from src.models import Candle, Signal, Tick


class Engine:
    def __init__(self, strategy_manager, risk_manager, executor, portfolio_manager, config):
        self._strategies = strategy_manager
        self._risk = risk_manager
        self._executor = executor
        self._portfolio = portfolio_manager
        self._config = config
        self._last_candle_close: float = 0.0

    def on_candle(self, candle: Candle) -> None:
        self._last_candle_close = candle.close
        self._strategies.on_candle(candle)
        for signal in self._strategies.collect_signals():
            self._process_signal(signal, candle.close)

    def on_tick(self, tick: Tick) -> None:
        self._strategies.on_tick(tick)
        triggered = self._portfolio.update_prices(tick.symbol, tick.ltp)
        for position in triggered:
            sell_signal = Signal(
                strategy=position.strategy,
                action="SELL",
                symbol=position.symbol,
                option_type=position.option_type,
                strike=position.strike,
                expiry=position.expiry,
                quantity=position.quantity,
                sl_price=position.sl_price,
                target_price=position.target_price,
                timestamp=datetime.now(),
                trade_type=position.trade_type,
                market_price=position.current_price,
            )
            self._executor.place_order(sell_signal)

    def square_off_intraday(self) -> None:
        for position in self._portfolio.get_intraday_positions():
            price = self._last_candle_close if self._last_candle_close > 0 else position.current_price
            sell_signal = Signal(
                strategy=position.strategy,
                action="SELL",
                symbol=position.symbol,
                option_type=position.option_type,
                strike=position.strike,
                expiry=position.expiry,
                quantity=position.quantity,
                sl_price=position.sl_price,
                target_price=position.target_price,
                timestamp=datetime.now(),
                trade_type=position.trade_type,
                market_price=price,
            )
            self._executor.place_order(sell_signal)
            self._portfolio.close_position(position.position_id, price, "square_off")

    def _process_signal(self, signal: Signal, market_price: float) -> None:
        approved, reason = self._risk.evaluate(
            signal,
            self._portfolio.get_open_positions(),
            self._portfolio.get_daily_pnl(),
            self._config.risk.account_capital,
        )
        if not approved:
            logger.debug(f"Signal rejected: {reason}")
            return
        priced_signal = dataclasses.replace(signal, market_price=market_price)
        signal_with_defaults = self._risk.apply_defaults(priced_signal, market_price)
        final_signal = dataclasses.replace(signal_with_defaults, market_price=market_price)
        order_id = self._executor.place_order(final_signal)
        from src.models import Position
        position = Position(
            position_id=order_id,
            strategy=final_signal.strategy,
            symbol=final_signal.symbol,
            option_type=final_signal.option_type,
            strike=final_signal.strike,
            expiry=final_signal.expiry,
            entry_price=market_price,
            quantity=final_signal.quantity,
            sl_price=final_signal.sl_price,
            target_price=final_signal.target_price,
            entry_time=final_signal.timestamp,
            trade_type=final_signal.trade_type,
        )
        self._portfolio.open_position(position)
