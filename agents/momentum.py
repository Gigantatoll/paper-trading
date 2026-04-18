from .base import BaseAgent
from config import WATCHLIST, MAX_POSITIONS


class MomentumAgent(BaseAgent):
    """
    Ranks all watchlist stocks by 10-period price momentum.
    Holds the top-5 positive-momentum names; exits anything that falls off the list
    or turns negative.
    """

    PERIOD = 10
    MIN_MOMENTUM = 0.005

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

        for symbol in list(self.portfolio.positions):
            if symbol not in top:
                m = scores.get(symbol, 0)
                if m < 0:
                    reason = (
                        f"{symbol} lost momentum: down {abs(m)*100:.2f}% over the last "
                        f"{self.PERIOD} hours. Selling to avoid further losses."
                    )
                else:
                    reason = (
                        f"{symbol} dropped out of the top {MAX_POSITIONS} momentum stocks "
                        f"(current momentum: {m*100:.2f}%). Rotating into stronger performers."
                    )
                self._sell(symbol, reason)

        for i, symbol in enumerate(top):
            m = scores[symbol]
            rank = ranked.index(symbol) + 1
            reason = (
                f"{symbol} is ranked #{rank} out of {len(scores)} stocks by momentum. "
                f"It gained {m*100:.2f}% over the last {self.PERIOD} hours, "
                f"showing strong upward price pressure."
            )
            self._buy(symbol, reason)
