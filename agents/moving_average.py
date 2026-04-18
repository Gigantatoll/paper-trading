from .base import BaseAgent
from config import WATCHLIST


class MovingAverageAgent(BaseAgent):
    """
    Buys when the 10-period MA is above the 30-period MA (bullish trend).
    Sells when the 10-period MA drops back below (bearish trend).
    """

    FAST = 10
    SLOW = 30

    def _execute_strategy(self, prices: dict):
        for symbol in WATCHLIST:
            fast, slow = self.market_data.moving_averages(symbol, self.FAST, self.SLOW)
            if fast is None or slow is None:
                continue

            bullish = fast > slow

            if bullish:
                reason = (
                    f"{symbol}'s {self.FAST}-hour average price (${fast:.2f}) is above "
                    f"its {self.SLOW}-hour average (${slow:.2f}). This means short-term "
                    f"momentum is stronger than the longer trend — a bullish signal."
                )
                self._buy(symbol, reason)

            elif not bullish and symbol in self.portfolio.positions:
                reason = (
                    f"{symbol}'s {self.FAST}-hour average (${fast:.2f}) dropped below "
                    f"its {self.SLOW}-hour average (${slow:.2f}). This crossover is a "
                    f"classic bearish signal — the short-term trend has turned down."
                )
                self._sell(symbol, reason)
