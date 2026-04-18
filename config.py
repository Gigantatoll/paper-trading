WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "MA",
    "UNH", "JNJ", "WMT", "PG", "XOM",
    "BAC", "HD", "AVGO", "MRK", "CVX",
    "ABBV", "COST", "PEP", "KO", "NFLX"
]

DIVIDEND_WATCHLIST = [
    "VZ", "T", "MO", "XOM", "CVX", "KO", "PEP",
    "JNJ", "PG", "ABBV", "MRK", "IBM", "SO", "DUK",
    "NEE", "O", "WBA", "DOW", "MMM", "PM"
]

UPDATE_INTERVAL  = 300    # seconds between agent cycles
MAX_POSITION_PCT = 0.20   # max 20% of portfolio per stock
MAX_POSITIONS    = 5      # max open positions per agent
STOP_LOSS_PCT    = 0.08   # sell if down 8% from entry
TAKE_PROFIT_PCT  = 0.15   # sell if up 15% from entry
DATA_DIR         = "data"
HIST_PERIOD      = "5d"
HIST_INTERVAL    = "1h"
