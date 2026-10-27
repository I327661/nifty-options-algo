from src.config import load_config


def test_config_loads_defaults():
    config = load_config()
    assert config.risk.lot_size == 65
    assert config.risk.max_capital_per_trade_pct == 0.02
    assert config.risk.daily_loss_limit_pct == 0.01
    assert config.risk.max_open_positions == 3
    assert config.risk.default_sl_pct == 0.30
    assert config.risk.default_target_pct == 0.60
    assert config.risk.illiquid_premium_threshold == 5.0
    assert config.risk.brokerage_per_order == 20.0
    assert config.broker.name == "fyers"
