from .base import BaseAgent
from config import DIVIDEND_WATCHLIST, MAX_POSITIONS


class DividendAgent(BaseAgent):
    """
    Focuses on high-dividend-yield stocks.
    Buys the top 5 highest-yielding stocks that also sit above their 30-period
    moving average (to avoid 'yield traps' — stocks with high yield because
    the price has crashed for a bad reason).
    Sells only when stop-loss or take-profit triggers (handled by base class).
    """

    MIN_YIELD = 0.02   # at least 2% annual dividend yield to qualify

    def _execute_strategy(self, prices: dict):
        # Score each stock: yield * price-above-MA bonus
        candidates = []
        for symbol in DIVIDEND_WATCHLIST:
            dy = self.market_data.dividend_yield(symbol)
            if dy is None or dy < self.MIN_YIELD:
                continue

            fast_ma, slow_ma = self.market_data.moving_averages(symbol, fast=10, slow=30)
            price = self.market_data.get_price(symbol)
            if not price:
                continue

            # Only buy if price is above the slow MA (healthy trend)
            above_ma = (slow_ma is None) or (price >= slow_ma)
            if above_ma:
                candidates.append((symbol, dy))

        if not candidates:
            return

        candidates.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, _ in candidates[:MAX_POSITIONS]]

        for symbol, dy in candidates[:MAX_POSITIONS]:
            price = self.market_data.get_price(symbol)
            _, slow_ma = self.market_data.moving_averages(symbol, fast=10, slow=30)
            ma_note = f" Its price (${price:.2f}) is above its 30-hour average (${slow_ma:.2f}), confirming a healthy trend." if slow_ma else ""
            reason = (
                f"{symbol} pays a {dy*100:.2f}% annual dividend yield, ranking it among "
                f"the top dividend payers on the watchlist.{ma_note} "
                f"Buying to collect steady income while holding."
            )
            self._buy(symbol, reason)
