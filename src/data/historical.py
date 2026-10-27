import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


class HistoricalDataManager:
    def __init__(self, fyers_client, cache_dir: str = "data/historical"):
        self._fyers = fyers_client
        self._cache_dir = Path(cache_dir)

    def _cache_path(self, symbol: str, timeframe: str, for_date: date) -> Path:
        safe_symbol = symbol.replace(":", "_").replace("/", "_")
        return self._cache_dir / safe_symbol / timeframe / f"{for_date.isoformat()}.parquet"

    def get_ohlcv(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        frames = []
        current = from_date
        while current <= to_date:
            path = self._cache_path(symbol, timeframe, current)
            if path.exists():
                frames.append(pd.read_parquet(path))
            else:
                df = self._fetch_from_api(symbol, current, current, timeframe)
                if df is not None and not df.empty:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    df.to_parquet(path, index=False)
                    frames.append(df)
            current += timedelta(days=1)

        if not frames:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        result = pd.concat(frames, ignore_index=True)
        if "timestamp" in result.columns:
            result["timestamp"] = pd.to_datetime(result["timestamp"], unit="s", utc=True)
            result = result.set_index("timestamp")
        return result

    def _fetch_from_api(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        timeframe_map = {"1m": "1", "5m": "5", "15m": "15", "1d": "D"}
        resolution = timeframe_map.get(timeframe, timeframe)
        import time
        from_ts = int(time.mktime(from_date.timetuple()))
        to_ts = int(time.mktime(to_date.timetuple())) + 86399
        data = self._fyers.history({
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",
            "range_from": str(from_ts),
            "range_to": str(to_ts),
            "cont_flag": "1",
        })
        candles = data.get("candles", [])
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        return df
