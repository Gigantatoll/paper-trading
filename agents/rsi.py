from .base import BaseAgent
from config import WATCHLIST


class RSIAgent(BaseAgent):
    """
    Buys stocks when RSI(14) dips below 35 (oversold).
    Sells when RSI climbs above 65 (overbought).
    """

    BUY_LEVEL = 35
    SELL_LEVEL = 65

    def _execute_strategy(self, prices: dict):
        for symbol in WATCHLIST:
            rsi = self.market_data.rsi(symbol)
            if rsi is None:
                continue

            if rsi < self.BUY_LEVEL:
                reason = (
                    f"{symbol}'s RSI is {rsi:.1f}, which is below {self.BUY_LEVEL}. "
                    f"RSI below 35 means the stock has been sold off heavily and is "
                    f"considered oversold — statistically likely to bounce back up."
                )
                self._buy(symbol, reason)

            elif rsi > self.SELL_LEVEL and symbol in self.portfolio.positions:
                reason = (
                    f"{symbol}'s RSI climbed to {rsi:.1f}, above {self.SELL_LEVEL}. "
                    f"RSI above 65 means the stock is overbought — buyers are exhausted "
                    f"and a pullback is likely. Selling to lock in gains."
                )
                self._sell(symbol, reason)
