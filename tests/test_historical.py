import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import date
from src.data.historical import HistoricalDataManager


def test_returns_dataframe_with_ohlcv_columns(tmp_path):
    mgr = HistoricalDataManager(fyers_client=MagicMock(), cache_dir=str(tmp_path))
    mock_df = pd.DataFrame({
        'timestamp': [1696214400], 'open': [19500.0], 'high': [19550.0],
        'low': [19480.0], 'close': [19520.0], 'volume': [1000]
    })
    with patch.object(mgr, '_fetch_from_api', return_value=mock_df):
        df = mgr.get_ohlcv("NSE:NIFTY50-INDEX", date(2023, 10, 2), date(2023, 10, 2), "5m")
    assert {'open', 'high', 'low', 'close', 'volume'}.issubset(df.columns)


def test_caches_to_parquet_on_first_fetch(tmp_path):
    mgr = HistoricalDataManager(fyers_client=MagicMock(), cache_dir=str(tmp_path))
    mock_df = pd.DataFrame({
        'timestamp': [1696214400], 'open': [19500.0], 'high': [19550.0],
        'low': [19480.0], 'close': [19520.0], 'volume': [1000]
    })
    with patch.object(mgr, '_fetch_from_api', return_value=mock_df):
        mgr.get_ohlcv("NSE:NIFTY50-INDEX", date(2023, 10, 2), date(2023, 10, 2), "5m")
    assert len(list(tmp_path.rglob("*.parquet"))) == 1


def test_uses_cache_on_second_call(tmp_path):
    mgr = HistoricalDataManager(fyers_client=MagicMock(), cache_dir=str(tmp_path))
    mock_df = pd.DataFrame({
        'timestamp': [1696214400], 'open': [19500.0], 'high': [19550.0],
        'low': [19480.0], 'close': [19520.0], 'volume': [1000]
    })
    with patch.object(mgr, '_fetch_from_api', return_value=mock_df) as mock_fetch:
        mgr.get_ohlcv("NSE:NIFTY50-INDEX", date(2023, 10, 2), date(2023, 10, 2), "5m")
        mgr.get_ohlcv("NSE:NIFTY50-INDEX", date(2023, 10, 2), date(2023, 10, 2), "5m")
    assert mock_fetch.call_count == 1
