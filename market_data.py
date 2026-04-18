from __future__ import annotations

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple
import pytz

from config import WATCHLIST, HIST_PERIOD, HIST_INTERVAL


class MarketData:
    def __init__(self):
        self.current_prices: dict = {}
        self._historical: dict = {}
        self._last_hist_update: Optional[datetime] = None
        self.status = "Initializing…"
        self.last_updated: Optional[datetime] = None

    # ------------------------------------------------------------------ #

    def update(self):
        self.status = "Fetching…"
        try:
            self._fetch_prices()
            # Refresh hourly
            if (
                self._last_hist_update is None
                or (datetime.now() - self._last_hist_update).seconds > 3600
            ):
                self._fetch_historical()
            self.last_updated = datetime.now()
            self.status = "Live ✓" if self.is_market_open() else "Market Closed"
        except Exception as exc:
            self.status = f"Error: {str(exc)[:40]}"

    def is_market_open(self) -> bool:
        ny = pytz.timezone("America/New_York")
        now = datetime.now(ny)
        if now.weekday() >= 5:
            return False
        open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return open_t <= now <= close_t

    # ------------------------------------------------------------------ #

    def get_price(self, symbol: str) -> Optional[float]:
        return self.current_prices.get(symbol)

    def get_history(self, symbol: str) -> pd.Series:
        return self._historical.get(symbol, pd.Series(dtype=float))

    # ------------------------------------------------------------------ #

    def rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        prices = self.get_history(symbol)
        if len(prices) < period + 1:
            return None
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        value = 100 - (100 / (1 + rs))
        return float(value.iloc[-1])

    def momentum(self, symbol: str, period: int = 10) -> Optional[float]:
        prices = self.get_history(symbol)
        if len(prices) < period + 1:
            return None
        return float(prices.pct_change(period).iloc[-1])

    def moving_averages(self, symbol: str, fast: int = 10, slow: int = 30) -> Tuple[Optional[float], Optional[float]]:
        prices = self.get_history(symbol)
        if len(prices) < slow:
            return None, None
        return (
            float(prices.rolling(fast).mean().iloc[-1]),
            float(prices.rolling(slow).mean().iloc[-1]),
        )

    # ------------------------------------------------------------------ #

    def _fetch_prices(self):
        data = yf.download(
            WATCHLIST, period="1d", interval="1m",
            progress=False, auto_adjust=True, threads=True,
        )
        if data.empty:
            return

        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        for symbol in WATCHLIST:
            if symbol in close.columns:
                series = close[symbol].dropna()
                if not series.empty:
                    self.current_prices[symbol] = float(series.iloc[-1])

    def _fetch_historical(self):
        data = yf.download(
            WATCHLIST, period=HIST_PERIOD, interval=HIST_INTERVAL,
            progress=False, auto_adjust=True, threads=True,
        )
        if data.empty:
            return

        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        for symbol in WATCHLIST:
            if symbol in close.columns:
                self._historical[symbol] = close[symbol].dropna()

        self._last_hist_update = datetime.now()
