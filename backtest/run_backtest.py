"""Backtest CLI: python -m backtest.run_backtest --from-date 2024-01-01 --to-date 2024-03-31"""
import argparse
import sys
from datetime import date, timedelta

from src.config import AppConfig
from src.data.symbol_resolver import SymbolResolver
from src.data.historical import HistoricalDataFetcher
from src.strategies.directional import DirectionalStrategy
from src.strategies.scalping import ScalpingStrategy
from src.strategies.systematic import SystematicStrategy
from src.strategies.manager import StrategyManager
from src.risk.manager import RiskManager
from src.execution.backtest import BacktestExecutor
from src.portfolio.trade_log import TradeLog
from src.portfolio.manager import PortfolioManager
from src.engine import Engine


def _parse_args():
    p = argparse.ArgumentParser(description="Nifty options backtest runner")
    p.add_argument("--from-date", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--to-date", required=True, help="End date YYYY-MM-DD")
    p.add_argument("--capital", type=float, default=100000.0, help="Account capital")
    p.add_argument("--strategy", default="all", choices=["all", "directional", "scalping", "systematic"])
    p.add_argument("--db", default="backtest_trades.db", help="SQLite output path")
    return p.parse_args()


def _build_strategies(cfg, symbol_resolver):
    strategies = []
    directional = DirectionalStrategy("directional", symbol_resolver=symbol_resolver)
    scalping = ScalpingStrategy("scalping", symbol_resolver=symbol_resolver)
    systematic = SystematicStrategy("systematic", cfg.strategies.get("systematic", {
        "entry_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "entry_time": "09:25",
        "option_type": "CE",
        "trade_type": "intraday",
        "sl_pct": 0.30,
        "target_pct": 0.60,
    }), symbol_resolver=symbol_resolver)
    return [directional, scalping, systematic]


def main():
    args = _parse_args()
    cfg = AppConfig()
    from_date = date.fromisoformat(args.from_date)
    to_date = date.fromisoformat(args.to_date)

    symbol_resolver = SymbolResolver()
    fetcher = HistoricalDataFetcher(cfg)
    trade_log = TradeLog(args.db, lot_size=cfg.risk.lot_size)
    portfolio = PortfolioManager(trade_log, lot_size=cfg.risk.lot_size)
    executor = BacktestExecutor(
        brokerage_per_order=cfg.risk.brokerage_per_order,
        lot_size=cfg.risk.lot_size,
    )
    strategy_manager = StrategyManager(_build_strategies(cfg, symbol_resolver))
    risk_manager = RiskManager(cfg)

    # Override account capital from CLI arg
    cfg.risk.__dict__["account_capital"] = args.capital

    engine = Engine(strategy_manager, risk_manager, executor, portfolio, cfg)

    current = from_date
    while current <= to_date:
        try:
            candles = fetcher.fetch("NSE:NIFTY50-INDEX", "5", current, current)
            for candle in candles:
                engine.on_candle(candle)
            engine.square_off_intraday()
            summary = trade_log.get_daily_summary(current)
            print(f"{current}: trades={summary['trades']} wins={summary['wins']} losses={summary['losses']} pnl={summary['net_pnl']:.2f}")
        except Exception as e:
            print(f"{current}: skipped ({e})", file=sys.stderr)
        current += timedelta(days=1)

    print(f"\nTotal brokerage: ₹{executor.total_brokerage:.2f}")


if __name__ == "__main__":
    main()
