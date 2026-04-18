#!/usr/bin/env python3
"""
Paper Trading System
Usage:
    python main.py --capital 10000          # start fresh with $10,000 each
    python main.py --capital 10000 --reset  # wipe saved state and restart
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

# Agents import relative to this file's directory
sys.path.insert(0, os.path.dirname(__file__))
from agents.momentum import MomentumAgent
from agents.rsi import RSIAgent
from agents.moving_average import MovingAverageAgent

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="Paper Trading System — fake money, real data")
    p.add_argument("--capital", type=float, required=True,
                   help="Starting capital per agent, e.g. 10000")
    p.add_argument("--reset", action="store_true",
                   help="Wipe saved portfolios and start fresh")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(DATA_DIR, exist_ok=True)

    console.print(f"\n[bold green]Paper Trading System[/bold green]")
    console.print(f"Starting capital per agent : [bold]${args.capital:,.2f}[/bold]")
    console.print(f"Update interval            : [bold]{UPDATE_INTERVAL // 60} min[/bold]")
    console.print(f"Watchlist                  : [bold]25 large-cap US stocks[/bold]")
    console.print(f"\n[dim]Fetching initial market data — this may take ~20 seconds…[/dim]\n")

    market_data = MarketData()

    agents = [
        MomentumAgent("Momentum Agent",    args.capital, market_data, args.reset),
        RSIAgent("RSI Agent",              args.capital, market_data, args.reset),
        MovingAverageAgent("MA Crossover", args.capital, market_data, args.reset),
    ]

    dashboard = Dashboard(agents, market_data)

    # Initial data fetch before entering Live mode
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

    console.print("\n[bold yellow]Stopped. All portfolios saved to ./data/[/bold yellow]")


if __name__ == "__main__":
    main()
