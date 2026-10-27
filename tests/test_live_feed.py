from unittest.mock import MagicMock, patch
from src.data.live_feed import LiveFeed
from src.models import Tick


def test_on_tick_callback_called_on_message():
    on_tick = MagicMock()
    feed = LiveFeed(MagicMock(), ["NSE:NIFTY50-INDEX"], on_candle=MagicMock(), on_tick=on_tick)
    feed._on_message({"type": "sf", "symbol": "NSE:NIFTY50-INDEX",
                      "ltp": 21500.0, "vol_traded_today": 1000, "tt": 1704167400})
    on_tick.assert_called_once()
    assert on_tick.call_args[0][0].ltp == 21500.0


def test_reconnect_increments_counter():
    feed = LiveFeed(MagicMock(), [], on_candle=MagicMock(), on_tick=MagicMock())
    with patch.object(feed, 'start'):
        feed._on_close("lost")
    assert feed._reconnect_attempts == 1


def test_candle_builders_preserved_on_reconnect():
    feed = LiveFeed(MagicMock(), ["NSE:NIFTY50-INDEX"], on_candle=MagicMock(), on_tick=MagicMock())
    feed._on_message({"type": "sf", "symbol": "NSE:NIFTY50-INDEX",
                      "ltp": 21500.0, "vol_traded_today": 100, "tt": 1704167400})
    builders_before = {k: v.get_current_state() for k, v in feed._candle_builders.items()}
    with patch.object(feed, 'start'):
        feed._on_close("lost")
    for key, state in builders_before.items():
        assert feed._candle_builders[key].get_current_state() == state
