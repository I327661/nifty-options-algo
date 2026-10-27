"""
Backtest using free Yahoo Finance data (no Fyers credentials needed).
Downloads Nifty 50 (^NSEI) 5-minute candles and runs all strategies.

Usage:
    python backtest_free.py --days 30
    python backtest_free.py --days 30 --capital 100000 --strategy directional
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta

import yfinance as yf

from src.config import AppConfig
from src.data.symbol_resolver import SymbolResolver
from src.models import Candle
from src.strategies.directional import DirectionalStrategy
from src.strategies.scalping import ScalpingStrategy
from src.strategies.manager import StrategyManager
from src.risk.manager import RiskManager
from src.execution.backtest import BacktestExecutor
from src.portfolio.trade_log import TradeLog
from src.portfolio.manager import PortfolioManager
from src.engine import Engine


def _parse_args():
    p = argparse.ArgumentParser(description="Free backtest using Yahoo Finance data")
    p.add_argument("--days", type=int, default=30, help="Number of past days to test (max 60 for 5m data)")
    p.add_argument("--capital", type=float, default=100000.0, help="Starting capital in INR")
    p.add_argument("--strategy", default="all",
                   choices=["all", "directional", "scalping"])
    p.add_argument("--db", default="backtest_free.db", help="SQLite output path")
    return p.parse_args()


def _download_nifty_data(days: int):
    print(f"Downloading Nifty 50 data for last {days} days from Yahoo Finance...")
    ticker = yf.Ticker("^NSEI")
    df = ticker.history(period=f"{days}d", interval="5m")
    if df.empty:
        print("ERROR: Could not download data. Check your internet connection.")
        sys.exit(1)
    df.index = df.index.tz_convert("Asia/Kolkata")
    print(f"Downloaded {len(df)} candles from {df.index[0].date()} to {df.index[-1].date()}")
    return df


def _build_strategies(cfg, symbol_resolver, strategy_filter):
    directional_params = {"ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "trade_type": "intraday"}
    scalping_params = {"trade_type": "intraday"}
    all_strategies = {
        "directional": DirectionalStrategy("directional", directional_params, symbol_resolver=symbol_resolver),
        "scalping": ScalpingStrategy("scalping", scalping_params, symbol_resolver=symbol_resolver),
    }
    if strategy_filter == "all":
        return list(all_strategies.values())
    return [all_strategies[strategy_filter]]


def main():
    args = _parse_args()
    if args.days > 60:
        print("WARNING: Yahoo Finance only provides 5m data for the last 60 days. Capping at 60.")
        args.days = 60

    cfg = AppConfig()
    cfg.risk.account_capital = args.capital

    # Always start fresh — remove stale db from prior runs
    if os.path.exists(args.db):
        os.remove(args.db)

    df = _download_nifty_data(args.days)

    symbol_resolver = SymbolResolver(fyers_client=None)
    trade_log = TradeLog(args.db, lot_size=cfg.risk.lot_size)
    portfolio = PortfolioManager(
        trade_log,
        lot_size=cfg.risk.lot_size,
        illiquid_threshold=cfg.risk.illiquid_premium_threshold,
    )
    executor = BacktestExecutor(
        brokerage_per_order=cfg.risk.brokerage_per_order,
        lot_size=cfg.risk.lot_size,
    )
    strategy_manager = StrategyManager(_build_strategies(cfg, symbol_resolver, args.strategy))
    risk_manager = RiskManager(cfg)
    engine = Engine(strategy_manager, risk_manager, executor, portfolio, cfg)

    current_day = None
    total_trades = total_wins = total_losses = 0
    total_pnl = 0.0

    for ts, row in df.iterrows():
        candle = Candle(
            symbol="NSE:NIFTY50-INDEX",
            timestamp=ts.to_pydatetime(),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
            timeframe="5m",
        )

        day = ts.date()
        if current_day is None:
            current_day = day

        if day != current_day:
            # End of previous day — square off and print summary
            engine.square_off_intraday()
            summary = trade_log.get_daily_summary(current_day)
            if summary["trades"] > 0:
                pnl_sign = "+" if summary["net_pnl"] >= 0 else ""
                print(f"  {current_day} ({current_day.strftime('%a')}):  "
                      f"trades={summary['trades']}  "
                      f"wins={summary['wins']}  losses={summary['losses']}  "
                      f"P&L={pnl_sign}{summary['net_pnl']:,.0f}")
                total_trades += summary["trades"]
                total_wins += summary["wins"]
                total_losses += summary["losses"]
                total_pnl += summary["net_pnl"]
            current_day = day
            portfolio.reset_daily()  # reset intraday P&L for new day

        portfolio.set_current_time(ts.to_pydatetime())
        engine.on_candle(candle)

    # Final day
    if current_day:
        engine.square_off_intraday()
        summary = trade_log.get_daily_summary(current_day)
        if summary["trades"] > 0:
            pnl_sign = "+" if summary["net_pnl"] >= 0 else ""
            print(f"  {current_day} ({current_day.strftime('%a')}):  "
                  f"trades={summary['trades']}  "
                  f"wins={summary['wins']}  losses={summary['losses']}  "
                  f"P&L={pnl_sign}{summary['net_pnl']:,.0f}")
            total_trades += summary["trades"]
            total_wins += summary["wins"]
            total_losses += summary["losses"]
            total_pnl += summary["net_pnl"]

    # Summary
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    brokerage = executor.total_brokerage
    net_after_brokerage = total_pnl - brokerage
    print()
    print("=" * 50)
    print(f"  Strategy:      {args.strategy}")
    print(f"  Capital:       Rs {args.capital:,.0f}")
    print(f"  Total trades:  {total_trades}")
    print(f"  Win rate:      {win_rate:.1f}%  ({total_wins}W / {total_losses}L)")
    print(f"  Gross P&L:     Rs {total_pnl:+,.0f}")
    print(f"  Brokerage:     Rs {brokerage:,.0f}")
    print(f"  Net P&L:       Rs {net_after_brokerage:+,.0f}")
    if args.capital > 0:
        print(f"  Return:        {net_after_brokerage / args.capital * 100:+.2f}%")
    print("=" * 50)

    if total_trades == 0:
        print()
        print("NOTE: No trades were generated.")
        print("The strategies need specific market conditions to trigger.")
        print("Try --days 60 for a longer period, or --strategy systematic")
        print("which trades every day at 9:25 AM.")


if __name__ == "__main__":
    main()
