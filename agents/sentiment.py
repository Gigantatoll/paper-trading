from .base import BaseAgent
from config import WATCHLIST, MAX_POSITIONS


class SentimentAgent(BaseAgent):
    """
    Reads the latest news headlines for each stock using Yahoo Finance,
    scores their sentiment with TextBlob (a natural language library),
    then buys the most positively covered stocks and sells ones with
    negative news coverage.

    Sentiment score: ranges from -1.0 (very negative) to +1.0 (very positive).
    Buy threshold:  > +0.05  (slightly positive news)
    Sell threshold: < -0.05  (slightly negative news)
    """

    BUY_THRESHOLD  =  0.05
    SELL_THRESHOLD = -0.05

    def _execute_strategy(self, prices: dict):
        scores = {}
        for symbol in WATCHLIST:
            s = self.market_data.sentiment_score(symbol)
            if s is not None:
                scores[symbol] = s

        if not scores:
            return

        # Sell positions where news has turned negative
        for symbol in list(self.portfolio.positions):
            score = scores.get(symbol)
            if score is not None and score < self.SELL_THRESHOLD:
                reason = (
                    f"News sentiment for {symbol} turned negative (score: {score:.2f} out of 1.0). "
                    f"Recent headlines are mostly pessimistic about this stock. "
                    f"Selling to avoid holding through a bad news cycle."
                )
                self._sell(symbol, reason)

        # Buy top positively-covered stocks
        positive = sorted(
            [(s, sc) for s, sc in scores.items() if sc > self.BUY_THRESHOLD],
            key=lambda x: x[1], reverse=True
        )
        for symbol, score in positive[:MAX_POSITIONS]:
            reason = (
                f"News sentiment for {symbol} is positive (score: {score:.2f} out of 1.0). "
                f"Recent news headlines are predominantly optimistic — analysts, earnings, "
                f"or product news are painting a good picture for this stock right now."
            )
            self._buy(symbol, reason)
