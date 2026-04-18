#!/usr/bin/env python3
"""
Generates a plain-English summary of all agent portfolios.
Output goes to 📊 Live Trading Data/Summary.txt
"""
import json
import os
from datetime import datetime

DATA_DIR = "data"
AGENT_NAMES = [
    "Momentum Agent",
    "RSI Agent",
    "MA Crossover",
    "Dividend Agent",
    "Sentiment Agent",
]


def load(name):
    path = os.path.join(DATA_DIR, f"{name.lower().replace(' ', '_')}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def main():
    lines = []
    lines.append("=" * 60)
    lines.append("  PAPER TRADING — LIVE SUMMARY")
    lines.append(f"  Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    for name in AGENT_NAMES:
        pf = load(name)
        if not pf:
            lines.append(f"\n{name}: no data yet")
            continue

        cash  = pf["cash"]
        start = pf["starting_capital"]
        pos_val = sum(p["shares"] * p["avg_price"] for p in pf.get("positions", {}).values())
        total = cash + pos_val
        pnl   = total - start
        pnl_pct = (pnl / start) * 100
        sign  = "+" if pnl >= 0 else ""
        trades = pf.get("trades", [])

        lines.append(f"\n{'─' * 60}")
        lines.append(f"  {name.upper()}")
        lines.append(f"{'─' * 60}")
        lines.append(f"  Portfolio value : ${total:,.2f}")
        lines.append(f"  Cash on hand    : ${cash:,.2f}")
        lines.append(f"  Started with    : ${start:,.2f}")
        lines.append(f"  Total P&L       : {sign}${pnl:,.2f}  ({sign}{pnl_pct:.2f}%)")
        lines.append(f"  Total trades    : {len(trades)}")

        positions = pf.get("positions", {})
        if positions:
            lines.append(f"\n  Open positions:")
            for sym, pos in positions.items():
                lines.append(f"    {sym}: {int(pos['shares'])} shares @ ${pos['avg_price']:.2f} entry")
        else:
            lines.append(f"\n  Open positions  : None")

        recent = [t for t in trades[-5:]][::-1]
        if recent:
            lines.append(f"\n  Last {len(recent)} trades:")
            for t in recent:
                ts     = t["time"][:16].replace("T", " ")
                action = t["action"]
                symbol = t["symbol"]
                price  = t["price"]
                reason = t.get("reason", "")
                pnl_note = ""
                if t["action"] == "SELL" and "trade_pnl" in t:
                    p = t["trade_pnl"]
                    pnl_note = f"  →  trade P&L: {'+' if p >= 0 else ''}{p:.2f}"
                lines.append(f"    [{ts}] {action} {symbol} @ ${price:.2f}{pnl_note}")
                if reason:
                    # Word-wrap the reason at 54 chars
                    words = reason.split()
                    line_buf = "      WHY: "
                    for word in words:
                        if len(line_buf) + len(word) + 1 > 60:
                            lines.append(line_buf)
                            line_buf = "            " + word + " "
                        else:
                            line_buf += word + " "
                    if line_buf.strip():
                        lines.append(line_buf)

    lines.append(f"\n{'=' * 60}")
    lines.append("  Full trade history: All Trades.csv (open in Excel)")
    lines.append("  Live website: https://gigantatoll.github.io/paper-trading/")
    lines.append("=" * 60)

    print("\n".join(lines))


if __name__ == "__main__":
    main()
