from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from portfolio import Portfolio
from config import MAX_POSITION_PCT, MAX_POSITIONS


class BaseAgent:
    def __init__(self, name: str, capital: float, market_data, reset: bool = False):
        self.name = name
        self.market_data = market_data
        self.portfolio = Portfolio(name, capital, reset)
        self.last_action: Optional[str] = None
        self.last_error: Optional[str] = None
        self.signal_log: list = []

    def run(self):
        prices = self.market_data.current_prices
        if not prices:
            return
        if not self.market_data.is_market_open():
            return
        try:
            self._execute_strategy(prices)
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)

    def _execute_strategy(self, prices: dict):
        raise NotImplementedError

    # ------------------------------------------------------------------ #

    def _buy(self, symbol: str, reason: str = ""):
        price = self.market_data.get_price(symbol)
        if not price:
            return
        if symbol in self.portfolio.positions:
            return
        if len(self.portfolio.positions) >= MAX_POSITIONS:
            return

        shares = self._shares_to_buy(price)
        if shares > 0 and self.portfolio.buy(symbol, shares, price):
            msg = f"BUY {shares}x {symbol} @ ${price:.2f}  [{reason}]"
            self.last_action = msg
            self._log(msg)

    def _sell(self, symbol: str, reason: str = ""):
        price = self.market_data.get_price(symbol)
        if not price or symbol not in self.portfolio.positions:
            return

        shares = self.portfolio.positions[symbol]["shares"]
        if self.portfolio.sell(symbol, shares, price):
            msg = f"SELL {shares}x {symbol} @ ${price:.2f}  [{reason}]"
            self.last_action = msg
            self._log(msg)

    def _shares_to_buy(self, price: float) -> int:
        prices = self.market_data.current_prices
        total = self.portfolio.total_value(prices)
        invest = min(total * MAX_POSITION_PCT, self.portfolio.cash * 0.95)
        if invest < price:
            return 0
        return math.floor(invest / price)

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M")
        self.signal_log.append(f"{ts}  {msg}")
        self.signal_log = self.signal_log[-12:]
