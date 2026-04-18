#!/usr/bin/env python3
"""
Generates docs/index.html — a live dashboard served via GitHub Pages.
Called automatically at the end of each trading cycle.
"""
import json
import os
from datetime import datetime

DATA_DIR = "data"
DOCS_DIR = "docs"
AGENT_NAMES = ["Momentum Agent", "RSI Agent", "MA Crossover"]
COLORS = {"Momentum Agent": "#f0883e", "RSI Agent": "#58a6ff", "MA Crossover": "#3fb950"}


def load_portfolio(name: str) -> dict:
    path = os.path.join(DATA_DIR, f"{name.lower().replace(' ', '_')}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_snapshots() -> list:
    path = os.path.join(DATA_DIR, "snapshots.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_snapshot(portfolios: dict):
    path = os.path.join(DATA_DIR, "snapshots.json")
    snapshots = load_snapshots()
    entry = {"time": datetime.utcnow().strftime("%Y-%m-%d %H:%M")}
    for name, pf in portfolios.items():
        if pf:
            # Value = cash + positions at avg price (no live prices in report gen)
            pos_value = sum(p["shares"] * p["avg_price"] for p in pf.get("positions", {}).values())
            entry[name] = round(pf["cash"] + pos_value, 2)
    snapshots.append(entry)
    snapshots = snapshots[-600:]  # ~2 months of 5-min intervals
    with open(path, "w") as f:
        json.dump(snapshots, f)


def build_agent_card(name: str, pf: dict) -> str:
    if not pf:
        return f'<div class="card"><h2>{name}</h2><p class="muted">No data yet</p></div>'

    cash = pf["cash"]
    start = pf["starting_capital"]
    pos_value = sum(p["shares"] * p["avg_price"] for p in pf.get("positions", {}).values())
    total = cash + pos_value
    pnl = total - start
    pnl_pct = (pnl / start) * 100
    color = "COLORS.get(name, '#fff')"
    sign = "+" if pnl >= 0 else ""
    pnl_class = "pos" if pnl >= 0 else "neg"

    positions_html = ""
    for sym, pos in pf.get("positions", {}).items():
        positions_html += f'<span class="tag">{sym} × {int(pos["shares"])}</span>'
    if not positions_html:
        positions_html = '<span class="muted">No open positions</span>'

    return f"""
    <div class="card" style="border-top: 3px solid {COLORS.get(name, '#888')}">
        <h2>{name}</h2>
        <div class="big-value">${total:,.2f}</div>
        <div class="pnl {pnl_class}">{sign}${pnl:,.2f} &nbsp;({sign}{pnl_pct:.2f}%)</div>
        <div class="meta">
            <span>Cash: ${cash:,.2f}</span>
            <span>Started: ${start:,.2f}</span>
        </div>
        <div class="positions">{positions_html}</div>
    </div>"""


def build_trade_rows(portfolios: dict) -> str:
    all_trades = []
    for name, pf in portfolios.items():
        for t in pf.get("trades", []):
            all_trades.append({**t, "agent": name})

    all_trades.sort(key=lambda x: x["time"], reverse=True)
    rows = ""
    for t in all_trades[:60]:
        ts = t["time"][5:16].replace("T", " ")
        action_class = "buy" if t["action"] == "BUY" else "sell"
        pnl_cell = ""
        if t["action"] == "SELL" and "trade_pnl" in t:
            p = t["trade_pnl"]
            pc = "pos" if p >= 0 else "neg"
            pnl_cell = f'<span class="{pc}">{("+" if p >= 0 else "")}{p:.2f}</span>'
        reason = t.get("reason", "—")
        rows += f"""
        <tr>
            <td class="muted">{ts}</td>
            <td>{t['agent']}</td>
            <td><span class="{action_class}">{t['action']}</span></td>
            <td><strong>{t['symbol']}</strong></td>
            <td>{int(t['shares'])}</td>
            <td>${t['price']:.2f}</td>
            <td>${t['total']:,.2f}</td>
            <td>{pnl_cell}</td>
            <td class="reason-cell">{reason}</td>
        </tr>"""
    if not rows:
        rows = '<tr><td colspan="9" class="muted" style="text-align:center;padding:20px">No trades yet — waiting for market open</td></tr>'
    return rows


def build_chart_data(snapshots: list) -> str:
    if not snapshots:
        return json.dumps({"labels": [], "datasets": []})

    labels = [s["time"][5:] for s in snapshots]  # MM-DD HH:MM
    datasets = []
    for name in AGENT_NAMES:
        values = [s.get(name) for s in snapshots]
        datasets.append({
            "label": name,
            "data": values,
            "borderColor": COLORS[name],
            "backgroundColor": COLORS[name] + "22",
            "fill": False,
            "tension": 0.3,
            "pointRadius": 2,
        })
    return json.dumps({"labels": labels, "datasets": datasets})


def generate():
    portfolios = {name: load_portfolio(name) for name in AGENT_NAMES}
    save_snapshot(portfolios)
    snapshots = load_snapshots()

    cards_html = "".join(build_agent_card(n, portfolios[n]) for n in AGENT_NAMES)
    trade_rows = build_trade_rows(portfolios)
    chart_data = build_chart_data(snapshots)
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<title>Paper Trading Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; max-width: 1400px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; font-weight: 700; }}
  .subtitle {{ color: #8b949e; font-size: 0.85rem; margin: 6px 0 28px; }}
  .cards {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; flex: 1; min-width: 260px; }}
  .card h2 {{ font-size: 0.9rem; color: #8b949e; margin-bottom: 10px; text-transform: uppercase; letter-spacing: .05em; }}
  .big-value {{ font-size: 2rem; font-weight: 700; margin-bottom: 4px; }}
  .pnl {{ font-size: 1rem; font-weight: 600; margin-bottom: 10px; }}
  .pos {{ color: #3fb950; }}
  .neg {{ color: #f85149; }}
  .meta {{ display: flex; gap: 14px; font-size: 0.8rem; color: #8b949e; margin-bottom: 10px; }}
  .positions {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
  .tag {{ background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; }}
  .muted {{ color: #8b949e; }}
  .chart-box {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 28px; }}
  .chart-box h2 {{ font-size: 0.9rem; color: #8b949e; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22; border: 1px solid #30363d; border-radius: 10px; overflow: hidden; font-size: 0.83rem; }}
  th {{ background: #21262d; padding: 10px 12px; text-align: left; font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: .05em; white-space: nowrap; }}
  td {{ padding: 10px 12px; border-top: 1px solid #21262d; vertical-align: top; }}
  .buy {{ color: #3fb950; font-weight: 700; }}
  .sell {{ color: #f85149; font-weight: 700; }}
  .reason-cell {{ color: #8b949e; font-size: 0.78rem; max-width: 420px; line-height: 1.4; }}
  h3 {{ font-size: 0.9rem; color: #8b949e; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 12px; }}
</style>
</head>
<body>
<h1>Paper Trading Dashboard</h1>
<p class="subtitle">Last updated: {updated} &nbsp;·&nbsp; Stock data delayed ~15 min (yfinance free tier) &nbsp;·&nbsp; Page auto-refreshes every 10 min</p>

<div class="cards">{cards_html}</div>

<div class="chart-box">
  <h2>Portfolio Value Over Time</h2>
  <canvas id="chart" height="70"></canvas>
</div>

<h3>Trade History &amp; Agent Reasoning</h3>
<table>
  <thead>
    <tr>
      <th>Time (UTC)</th><th>Agent</th><th>Action</th><th>Stock</th>
      <th>Shares</th><th>Price</th><th>Total</th><th>Trade P&amp;L</th><th>Why the agent did this</th>
    </tr>
  </thead>
  <tbody>{trade_rows}</tbody>
</table>

<script>
const chartData = {chart_data};
const ctx = document.getElementById('chart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{ labels: chartData.labels, datasets: chartData.datasets }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{ legend: {{ labels: {{ color: '#e6edf3', boxWidth: 12 }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 12 }}, grid: {{ color: '#21262d' }} }},
      y: {{ ticks: {{ color: '#8b949e', callback: v => '$' + v.toLocaleString() }}, grid: {{ color: '#21262d' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"Dashboard generated → {DOCS_DIR}/index.html")


if __name__ == "__main__":
    generate()
