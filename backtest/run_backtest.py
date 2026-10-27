"""Backtest CLI: python -m backtest.run_backtest --from-date 2024-01-01 --to-date 2024-03-31"""
import argparse
import sys
from datetime import date, timedelta

from src.config import AppConfig
from src.data.historical import HistoricalDataManager
from src.data.symbol_resolver import SymbolResolver
from src.models import Candle
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


def _build_strategies(cfg, symbol_resolver, strategy_filter: str = "all"):
    directional_params = {"ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "trade_type": "intraday"}
    scalping_params = {"trade_type": "intraday"}
    systematic_params = {
        "entry_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "entry_time": "09:25",
        "option_type": "CE",
        "trade_type": "intraday",
        "sl_pct": cfg.risk.default_sl_pct,
        "target_pct": cfg.risk.default_target_pct,
    }
    all_strategies = {
        "directional": DirectionalStrategy("directional", directional_params, symbol_resolver=symbol_resolver),
        "scalping": ScalpingStrategy("scalping", scalping_params, symbol_resolver=symbol_resolver),
        "systematic": SystematicStrategy("systematic", systematic_params, symbol_resolver=symbol_resolver),
    }
    if strategy_filter == "all":
        return list(all_strategies.values())
    return [all_strategies[strategy_filter]]


def main():
    args = _parse_args()
    cfg = AppConfig()
    cfg.risk.account_capital = args.capital
    from_date = date.fromisoformat(args.from_date)
    to_date = date.fromisoformat(args.to_date)

    # Pass None as fyers_client — backtest replays from cache, no live API needed
    symbol_resolver = SymbolResolver(fyers_client=None)
    fetcher = HistoricalDataManager(fyers_client=None)
    trade_log = TradeLog(args.db, lot_size=cfg.risk.lot_size)
    portfolio = PortfolioManager(trade_log, lot_size=cfg.risk.lot_size)
    executor = BacktestExecutor(
        brokerage_per_order=cfg.risk.brokerage_per_order,
        lot_size=cfg.risk.lot_size,
    )
    strategy_manager = StrategyManager(_build_strategies(cfg, symbol_resolver, args.strategy))
    risk_manager = RiskManager(cfg)
    engine = Engine(strategy_manager, risk_manager, executor, portfolio, cfg)

    current = from_date
    while current <= to_date:
        try:
            df = fetcher.get_ohlcv("NSE:NIFTY50-INDEX", current, current, "5")
            if df.empty:
                current += timedelta(days=1)
                continue
            df_reset = df.reset_index()
            ts_col = "timestamp" if "timestamp" in df_reset.columns else df_reset.columns[0]
            for row in df_reset.itertuples(index=False):
                ts = getattr(row, ts_col)
                candle = Candle(
                    symbol="NSE:NIFTY50-INDEX",
                    timestamp=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=int(row.volume),
                    timeframe="5m",
                )
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
