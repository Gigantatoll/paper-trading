#!/usr/bin/env python3
"""
Headless runner for GitHub Actions.
Runs one full trading cycle and exits — no live dashboard.
"""
import argparse
import os
import sys
import json
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(__file__))

from config import DATA_DIR
from market_data import MarketData
from agents.momentum import MomentumAgent
from agents.rsi import RSIAgent
from agents.moving_average import MovingAverageAgent
from agents.dividend import DividendAgent
from agents.sentiment import SentimentAgent

DEFAULT_CAPITAL = 300.0
STATE_FILE = os.path.join(DATA_DIR, "config.json")


def load_starting_capital() -> float:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("starting_capital", DEFAULT_CAPITAL)
    return DEFAULT_CAPITAL


def save_starting_capital(capital: float):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"starting_capital": capital}, f)


def log(msg: str):
    ts = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S ET")
    print(f"[{ts}] {msg}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capital", type=float, default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    capital = args.capital if args.capital else load_starting_capital()
    if args.capital:
        save_starting_capital(capital)

    log(f"=== Paper Trading Cycle — ${capital:,.2f} per agent ===")

    market_data = MarketData()
    agents = [
        MomentumAgent("Momentum Agent", capital, market_data, args.reset),
        RSIAgent("RSI Agent",           capital, market_data, args.reset),
        MovingAverageAgent("MA Crossover", capital, market_data, args.reset),
        DividendAgent("Dividend Agent", capital, market_data, args.reset),
        SentimentAgent("Sentiment Agent", capital, market_data, args.reset),
    ]

    log("Fetching market data…")
    market_data.update()
    log(f"Market status: {market_data.status} | Prices: {len(market_data.current_prices)} symbols | Sentiment: {len(market_data._sentiment_scores)} scores")

    if not market_data.current_prices:
        log("No price data — skipping cycle.")
        return

    for agent in agents:
        log(f"--- {agent.name} ---")
        agent.run()
        prices = market_data.current_prices
        pf = agent.portfolio
        tv  = pf.total_value(prices)
        pnl = pf.pnl(prices)
        log(f"  Value: ${tv:,.2f}  Cash: ${pf.cash:,.2f}  P&L: {'+' if pnl>=0 else ''}{pnl:.2f}")
        log(f"  Positions: {list(pf.positions.keys()) or 'none'}")
        if agent.last_action:
            log(f"  Action: {agent.last_action}")

    log("Generating dashboard and CSV…")
    from generate_report import generate
    generate()
    log("=== Cycle complete ===")


if __name__ == "__main__":
    main()
