from datetime import datetime, date
from unittest.mock import MagicMock
from src.strategies.systematic import SystematicStrategy
from src.strategies.manager import StrategyManager
from src.risk.manager import RiskManager
from src.execution.backtest import BacktestExecutor
from src.portfolio.trade_log import TradeLog
from src.portfolio.manager import PortfolioManager
from src.engine import Engine
from src.models import Candle


def test_full_pipeline_smoke(tmp_path):
    cfg = MagicMock()
    cfg.risk.lot_size = 65
    cfg.risk.max_capital_per_trade_pct = 0.02
    cfg.risk.daily_loss_limit_pct = 0.01
    cfg.risk.max_open_positions = 3
    cfg.risk.default_sl_pct = 0.30
    cfg.risk.default_target_pct = 0.60
    cfg.risk.illiquid_premium_threshold = 5.0
    cfg.risk.brokerage_per_order = 20.0
    cfg.risk.account_capital = 100000.0

    resolver = MagicMock()
    resolver.get_current_expiry.return_value = date(2024, 10, 28)
    resolver.get_atm_symbol.return_value = "NSE:NIFTY2410282150CE"

    strategy = SystematicStrategy("sys", {
        "entry_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "entry_time": "09:25",
        "option_type": "CE",
        "trade_type": "intraday",
        "sl_pct": 0.50,
        "target_pct": 1.0,
    }, symbol_resolver=resolver)

    engine = Engine(
        StrategyManager([strategy]),
        RiskManager(cfg),
        BacktestExecutor(),
        PortfolioManager(TradeLog(str(tmp_path / "t.db"))),
        cfg,
    )

    for i in range(10):
        engine.on_candle(Candle(
            "NSE:NIFTY50-INDEX", datetime(2024, 10, 28, 9, 20 + i, 0),
            21500.0, 21550.0, 21490.0, 21530.0, 1000, "1m",
        ))
    # must not raise
