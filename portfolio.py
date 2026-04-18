import json
import os
import math
from datetime import datetime
from config import DATA_DIR


class Portfolio:
    def __init__(self, name: str, starting_capital: float, reset: bool = False):
        self.name = name
        self.file_path = os.path.join(DATA_DIR, f"{name.lower().replace(' ', '_')}.json")

        if reset or not os.path.exists(self.file_path):
            self.cash = starting_capital
            self.starting_capital = starting_capital
            self.positions: dict = {}   # {symbol: {shares, avg_price}}
            self.trades: list = []
        else:
            self._load()

    # ------------------------------------------------------------------ #

    def buy(self, symbol: str, shares: int, price: float) -> bool:
        cost = shares * price
        if cost > self.cash or shares <= 0:
            return False

        self.cash -= cost
        if symbol in self.positions:
            existing = self.positions[symbol]
            total_shares = existing["shares"] + shares
            total_cost = existing["shares"] * existing["avg_price"] + cost
            self.positions[symbol] = {"shares": total_shares, "avg_price": total_cost / total_shares}
        else:
            self.positions[symbol] = {"shares": shares, "avg_price": price}

        self.trades.append({
            "time": datetime.now().isoformat(),
            "action": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": cost,
        })
        self._save()
        return True

    def sell(self, symbol: str, shares: int, price: float) -> bool:
        if symbol not in self.positions or self.positions[symbol]["shares"] < shares:
            return False

        revenue = shares * price
        self.cash += revenue
        self.positions[symbol]["shares"] -= shares
        if self.positions[symbol]["shares"] == 0:
            del self.positions[symbol]

        self.trades.append({
            "time": datetime.now().isoformat(),
            "action": "SELL",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": revenue,
        })
        self._save()
        return True

    # ------------------------------------------------------------------ #

    def total_value(self, prices: dict) -> float:
        value = self.cash
        for symbol, pos in self.positions.items():
            value += pos["shares"] * prices.get(symbol, pos["avg_price"])
        return value

    def pnl(self, prices: dict) -> float:
        return self.total_value(prices) - self.starting_capital

    def pnl_pct(self, prices: dict) -> float:
        return (self.pnl(prices) / self.starting_capital) * 100

    # ------------------------------------------------------------------ #

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump({
                "name": self.name,
                "cash": self.cash,
                "starting_capital": self.starting_capital,
                "positions": self.positions,
                "trades": self.trades[-200:],
            }, f, indent=2)

    def _load(self):
        with open(self.file_path) as f:
            data = json.load(f)
        self.cash = data["cash"]
        self.starting_capital = data["starting_capital"]
        self.positions = data["positions"]
        self.trades = data.get("trades", [])
