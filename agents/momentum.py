from .base import BaseAgent
from config import WATCHLIST, MAX_POSITIONS


class MomentumAgent(BaseAgent):
    """
    Ranks all watchlist stocks by 10-period price momentum.
    Holds the top-5 positive-momentum names; exits anything that falls off the list
    or turns negative.
    """

    PERIOD = 10
    MIN_MOMENTUM = 0.005   # at least +0.5% to qualify as a buy

    def _execute_strategy(self, prices: dict):
        scores = {}
        for symbol in WATCHLIST:
            m = self.market_data.momentum(symbol, self.PERIOD)
            if m is not None:
                scores[symbol] = m

        if not scores:
            return

        ranked = sorted(scores, key=lambda s: scores[s], reverse=True)
        top = [s for s in ranked[:MAX_POSITIONS] if scores[s] >= self.MIN_MOMENTUM]

        # Exit positions no longer in the top list
        for symbol in list(self.portfolio.positions):
            if symbol not in top:
                self._sell(symbol, f"momentum dropped ({scores.get(symbol, 0):.3f})")

        # Enter new top-list positions
        for symbol in top:
            self._buy(symbol, f"momentum={scores[symbol]:.3f}")
