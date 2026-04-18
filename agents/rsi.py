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
                self._buy(symbol, f"RSI={rsi:.1f} oversold")
            elif rsi > self.SELL_LEVEL and symbol in self.portfolio.positions:
                self._sell(symbol, f"RSI={rsi:.1f} overbought")
