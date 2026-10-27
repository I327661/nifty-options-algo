"""Live trading entry point for Nifty options algo."""
import sys
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler

from src.config import AppConfig
from src.data.symbol_resolver import SymbolResolver
from src.data.live_feed import LiveFeed
from src.strategies.directional import DirectionalStrategy
from src.strategies.scalping import ScalpingStrategy
from src.strategies.systematic import SystematicStrategy
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
        client_id=cfg.broker.client_id,
        token=cfg.broker.access_token,
        log_path="",
    )

    symbol_resolver = SymbolResolver()
    trade_log = TradeLog("live_trades.db", lot_size=cfg.risk.lot_size)
    portfolio = PortfolioManager(trade_log, lot_size=cfg.risk.lot_size)
    executor = LiveExecutor(fyers_client, lot_size=cfg.risk.lot_size)

    systematic_cfg = {
        "entry_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "entry_time": "09:25",
        "option_type": "CE",
        "trade_type": "intraday",
        "sl_pct": cfg.risk.default_sl_pct,
        "target_pct": cfg.risk.default_target_pct,
    }
    strategies = [
        DirectionalStrategy("directional", symbol_resolver=symbol_resolver),
        ScalpingStrategy("scalping", symbol_resolver=symbol_resolver),
        SystematicStrategy("systematic", systematic_cfg, symbol_resolver=symbol_resolver),
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
