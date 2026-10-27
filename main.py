"""Live trading entry point for Nifty options algo."""
import sys
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler

from src.config import AppConfig
from src.data.symbol_resolver import SymbolResolver
from src.data.live_feed import LiveFeed
from src.strategies.directional import DirectionalStrategy
from src.strategies.scalping import ScalpingStrategy
from src.strategies.manager import StrategyManager
from src.risk.manager import RiskManager
from src.execution.live import LiveExecutor
from src.portfolio.trade_log import TradeLog
from src.portfolio.manager import PortfolioManager
from src.engine import Engine


def main():
    cfg = AppConfig()
    logger.info("Starting Nifty options algo")

    from fyers_apiv3 import fyersModel
    fyers_client = fyersModel.FyersModel(
        client_id=cfg.broker.app_id,
        token=cfg.broker.access_token,
        log_path="",
    )

    symbol_resolver = SymbolResolver(fyers_client)
    trade_log = TradeLog("live_trades.db", lot_size=cfg.risk.lot_size)
    portfolio = PortfolioManager(trade_log, lot_size=cfg.risk.lot_size)
    executor = LiveExecutor(fyers_client, lot_size=cfg.risk.lot_size)

    directional_params = {
        "ema_fast": 9, "ema_slow": 21, "rsi_period": 14,
        "trade_type": "intraday",
    }
    scalping_params = {"trade_type": "intraday"}
    strategies = [
        DirectionalStrategy("directional", directional_params, symbol_resolver=symbol_resolver),
        ScalpingStrategy("scalping", scalping_params, symbol_resolver=symbol_resolver),
    ]
    strategy_manager = StrategyManager(strategies)
    risk_manager = RiskManager(cfg)
    engine = Engine(strategy_manager, risk_manager, executor, portfolio, cfg)

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(engine.square_off_intraday, "cron", hour=15, minute=15)
    scheduler.start()
    logger.info("Scheduler started — square-off at 15:15 IST")

    live_feed = LiveFeed(
        fyers_client=fyers_client,
        symbols=["NSE:NIFTY50-INDEX"],
        on_candle=engine.on_candle,
        on_tick=engine.on_tick,
    )
    try:
        live_feed.start()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        scheduler.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
