from datetime import date
from src.data.symbol_resolver import SymbolResolver


def test_atm_strike_rounds_to_nearest_50_down():
    r = SymbolResolver(fyers_client=None)
    assert r._round_to_atm_strike(21567.0) == 21550


def test_atm_strike_rounds_to_nearest_50_up():
    r = SymbolResolver(fyers_client=None)
    assert r._round_to_atm_strike(21576.0) == 21600


def test_symbol_format():
    r = SymbolResolver(fyers_client=None)
    symbol = r._build_symbol(21550, "CE", date(2024, 10, 31))
    assert symbol == "NSE:NIFTY241031 21550CE".replace(" ", "")


def test_symbol_format_expiry_day_same_as_today():
    r = SymbolResolver(fyers_client=None)
    today = date(2024, 10, 31)
    symbol = r._build_symbol(21500, "CE", today)
    assert "NIFTY" in symbol
    assert "CE" in symbol
    assert "21500" in symbol


def test_symbol_format_single_digit_month():
    r = SymbolResolver(fyers_client=None)
    symbol = r._build_symbol(21550, "PE", date(2024, 1, 4))
    assert symbol == "NSE:NIFTY240104 21550PE".replace(" ", "")
