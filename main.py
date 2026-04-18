#!/usr/bin/env python3
"""
Paper Trading System — local terminal dashboard
Usage:
    python3 main.py --capital 300           # start / resume
    python3 main.py --capital 300 --reset   # wipe saved state and restart
"""
import argparse
import os
import sys
import time

from rich.console import Console
from rich.live import Live

from config import DATA_DIR, UPDATE_INTERVAL
from dashboard import Dashboard
from market_data import MarketData

sys.path.insert(0, os.path.dirname(__file__))
from agents.momentum import MomentumAgent
from agents.rsi import RSIAgent
from agents.moving_average import MovingAverageAgent
from agents.dividend import DividendAgent
from agents.sentiment import SentimentAgent

console = Console()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--capital", type=float, required=True)
    p.add_argument("--reset",   action="store_true")
    args = p.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    console.print(f"\n[bold green]Paper Trading System[/bold green]")
    console.print(f"Capital per agent : [bold]${args.capital:,.2f}[/bold]")
    console.print(f"Agents            : [bold]5[/bold] (Momentum, RSI, MA Crossover, Dividend, Sentiment)")
    console.print(f"Update interval   : [bold]{UPDATE_INTERVAL // 60} min[/bold]")
    console.print(f"\n[dim]Fetching initial market data — may take ~30 seconds…[/dim]\n")

    market_data = MarketData()
    agents = [
        MomentumAgent("Momentum Agent",   args.capital, market_data, args.reset),
        RSIAgent("RSI Agent",             args.capital, market_data, args.reset),
        MovingAverageAgent("MA Crossover",args.capital, market_data, args.reset),
        DividendAgent("Dividend Agent",   args.capital, market_data, args.reset),
        SentimentAgent("Sentiment Agent", args.capital, market_data, args.reset),
    ]

    dashboard = Dashboard(agents, market_data)
    market_data.update()
    for agent in agents:
        agent.run()

    last_cycle = time.time()
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    with Live(dashboard.render(), refresh_per_second=1, screen=True) as live:
        try:
            while True:
                elapsed = time.time() - last_cycle
                dashboard.next_update_in = max(0, int(UPDATE_INTERVAL - elapsed))
                if elapsed >= UPDATE_INTERVAL:
                    market_data.update()
                    for agent in agents:
                        agent.run()
                    last_cycle = time.time()
                live.update(dashboard.render())
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    for agent in agents:
        agent.portfolio._save()
    console.print("\n[bold yellow]Stopped. All portfolios saved.[/bold yellow]")


if __name__ == "__main__":
    main()
