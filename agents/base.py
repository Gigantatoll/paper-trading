from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from portfolio import Portfolio
from config import MAX_POSITIONS, STOP_LOSS_PCT, TAKE_PROFIT_PCT


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
            self._check_risk_rules(prices)
            self._execute_strategy(prices)
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)

    def _execute_strategy(self, prices: dict):
        raise NotImplementedError

    # ------------------------------------------------------------------ #

    def _check_risk_rules(self, prices: dict):
        """Stop-loss and take-profit — runs before any strategy logic."""
        for symbol in list(self.portfolio.positions):
            pos = self.portfolio.positions[symbol]
            price = prices.get(symbol)
            if not price:
                continue
            change = (price - pos["avg_price"]) / pos["avg_price"]

            if change <= -STOP_LOSS_PCT:
                reason = (
                    f"STOP-LOSS: {symbol} dropped {abs(change)*100:.1f}% from the entry price "
                    f"(bought at ${pos['avg_price']:.2f}, now ${price:.2f}). "
                    f"Selling automatically to protect capital before losses grow further."
                )
                self._sell(symbol, reason)

            elif change >= TAKE_PROFIT_PCT:
                reason = (
                    f"TAKE-PROFIT: {symbol} is up {change*100:.1f}% from the entry price "
                    f"(bought at ${pos['avg_price']:.2f}, now ${price:.2f}). "
                    f"Locking in the gain before the price can reverse."
                )
                self._sell(symbol, reason)

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
        if shares > 0 and self.portfolio.buy(symbol, shares, price, reason):
            msg = f"BUY {shares}x {symbol} @ ${price:.2f}"
            self.last_action = msg
            self._log(msg)

    def _sell(self, symbol: str, reason: str = ""):
        price = self.market_data.get_price(symbol)
        if not price or symbol not in self.portfolio.positions:
            return

        shares = self.portfolio.positions[symbol]["shares"]
        if self.portfolio.sell(symbol, shares, price, reason):
            msg = f"SELL {shares}x {symbol} @ ${price:.2f}"
            self.last_action = msg
            self._log(msg)

    def _shares_to_buy(self, price: float) -> int:
        # Split remaining cash equally across remaining position slots — no per-stock cap
        slots_used = len(self.portfolio.positions)
        slots_left = max(1, MAX_POSITIONS - slots_used)
        invest = (self.portfolio.cash / slots_left) * 0.99
        if invest < price:
            return 0
        return math.floor(invest / price)

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M")
        self.signal_log.append(f"{ts}  {msg}")
        self.signal_log = self.signal_log[-12:]
