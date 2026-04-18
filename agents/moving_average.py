from .base import BaseAgent
from config import WATCHLIST


class MovingAverageAgent(BaseAgent):
    """
    Buys when the 10-period MA is above the 30-period MA (bullish).
    Sells when the 10-period MA drops back below the 30-period MA (bearish).
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
                self._buy(symbol, f"MA{self.FAST}({fast:.2f}) > MA{self.SLOW}({slow:.2f})")
            elif not bullish and symbol in self.portfolio.positions:
                self._sell(symbol, f"MA{self.FAST}({fast:.2f}) < MA{self.SLOW}({slow:.2f})")
