import sqlite3
from datetime import date, datetime
from typing import Optional

from src.models import Position


class TradeLog:
    def __init__(self, db_path: str, lot_size: int = 65):
        self._db_path = db_path
        self._lot_size = lot_size
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT,
                    symbol TEXT,
                    option_type TEXT,
                    strike INTEGER,
                    expiry TEXT,
                    entry_time TEXT,
                    entry_price REAL,
                    exit_time TEXT,
                    exit_price REAL,
                    quantity INTEGER,
                    pnl REAL,
                    exit_reason TEXT
                )
            """)

    def log_trade_closed(
        self,
        position: Position,
        exit_price: float,
        exit_reason: str,
        exit_time: datetime,
    ) -> None:
        pnl = (exit_price - position.entry_price) * position.quantity * self._lot_size
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trades
                    (strategy, symbol, option_type, strike, expiry,
                     entry_time, entry_price, exit_time, exit_price, quantity, pnl, exit_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position.strategy,
                    position.symbol,
                    position.option_type,
                    position.strike,
                    position.expiry.isoformat(),
                    position.entry_time.isoformat(),
                    position.entry_price,
                    exit_time.isoformat(),
                    exit_price,
                    position.quantity,
                    pnl,
                    exit_reason,
                ),
            )

    def get_trades(self, from_date: Optional[date] = None) -> list:
        query = "SELECT * FROM trades"
        params: list = []
        if from_date is not None:
            query += " WHERE DATE(exit_time) = ?"
            params.append(from_date.isoformat())
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_daily_summary(self, for_date: date) -> dict:
        trades = self.get_trades(for_date)
        net_pnl = sum(t["pnl"] for t in trades)
        wins = sum(1 for t in trades if t["pnl"] > 0)
        losses = sum(1 for t in trades if t["pnl"] <= 0)
        return {"trades": len(trades), "wins": wins, "losses": losses, "net_pnl": net_pnl}
