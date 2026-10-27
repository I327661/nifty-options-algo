from datetime import date, timedelta


class SymbolResolver:
    def __init__(self, fyers_client):
        self._fyers = fyers_client

    def _round_to_atm_strike(self, spot: float) -> int:
        return int(round(spot / 50) * 50)

    def _build_symbol(self, strike: int, option_type: str, expiry) -> str:
        date_str = expiry.strftime("%y%m%d")
        return f"NSE:NIFTY{date_str}{strike}{option_type}"

    def get_current_expiry(self, as_of: date = None):
        """Return nearest weekly Thursday expiry. Uses Fyers API if available, else computes locally."""
        if self._fyers is not None:
            try:
                data = self._fyers.optionchain({"symbol": "NSE:NIFTY50-INDEX", "strikecount": 1})
                expiry_str = data["data"]["expiryData"][0]["expiry"]
                from datetime import datetime
                return datetime.strptime(expiry_str, "%d-%b-%Y").date()
            except Exception:
                pass
        # Fallback: compute nearest Thursday (Nifty weekly expiry day)
        today = as_of or date.today()
        days_until_thursday = (3 - today.weekday()) % 7  # 3 = Thursday
        if days_until_thursday == 0:
            days_until_thursday = 7  # already Thursday — use next week
        return today + timedelta(days=days_until_thursday)

    def get_atm_symbol(self, spot_price: float, option_type: str, expiry) -> str:
        strike = self._round_to_atm_strike(spot_price)
        return self._build_symbol(strike, option_type, expiry)

