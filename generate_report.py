#!/usr/bin/env python3
"""
Generates:
  docs/index.html  — GitHub Pages live dashboard
  data/trades.csv  — running trade log, updated each cycle (not recreated)
"""
import csv
import json
import os
from datetime import datetime

DATA_DIR = "data"
DOCS_DIR = "docs"

AGENT_NAMES = [
    "Momentum Agent",
    "RSI Agent",
    "MA Crossover",
    "Dividend Agent",
    "Sentiment Agent",
]
COLORS = {
    "Momentum Agent":  "#f0883e",
    "RSI Agent":       "#58a6ff",
    "MA Crossover":    "#3fb950",
    "Dividend Agent":  "#d2a8ff",
    "Sentiment Agent": "#ffa657",
}


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

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
            pos_val = sum(p["shares"] * p["avg_price"] for p in pf.get("positions", {}).values())
            entry[name] = round(pf["cash"] + pos_val, 2)
    snapshots.append(entry)
    snapshots = snapshots[-1000:]
    with open(path, "w") as f:
        json.dump(snapshots, f)


# ─────────────────────────────────────────────────────────────────────────────
# CSV — updated in place, never recreated from scratch
# ─────────────────────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(DATA_DIR, "trades.csv")
CSV_FIELDS = ["time", "agent", "action", "symbol", "shares", "price", "total", "trade_pnl", "reason"]


def update_csv(portfolios: dict):
    # Load existing rows so we can skip already-written trades
    existing_keys: set = set()
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_keys.add((row["time"], row["agent"], row["action"], row["symbol"]))

    new_rows = []
    for name, pf in portfolios.items():
        for t in pf.get("trades", []):
            ts = t["time"][:16].replace("T", " ")
            key = (ts, name, t["action"], t["symbol"])
            if key not in existing_keys:
                new_rows.append({
                    "time":      ts,
                    "agent":     name,
                    "action":    t["action"],
                    "symbol":    t["symbol"],
                    "shares":    int(t["shares"]),
                    "price":     round(t["price"], 4),
                    "total":     round(t["total"], 2),
                    "trade_pnl": t.get("trade_pnl", ""),
                    "reason":    t.get("reason", ""),
                })

    if not new_rows and os.path.exists(CSV_PATH):
        return  # nothing new to write

    write_header = not os.path.exists(CSV_PATH)
    new_rows.sort(key=lambda r: r["time"])

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"CSV updated — {len(new_rows)} new row(s) appended → {CSV_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# HTML dashboard
# ─────────────────────────────────────────────────────────────────────────────

def build_agent_card(name: str, pf: dict) -> str:
    if not pf:
        return f'<div class="card" style="border-top:3px solid {COLORS.get(name,"#888")}"><h2>{name}</h2><p class="muted">No data yet</p></div>'

    cash  = pf["cash"]
    start = pf["starting_capital"]
    pos_val = sum(p["shares"] * p["avg_price"] for p in pf.get("positions", {}).values())
    total = cash + pos_val
    pnl   = total - start
    pnl_pct = (pnl / start) * 100
    sign  = "+" if pnl >= 0 else ""
    pc    = "pos" if pnl >= 0 else "neg"

    positions_html = "".join(
        f'<span class="tag">{sym} × {int(pos["shares"])}</span>'
        for sym, pos in pf.get("positions", {}).items()
    ) or '<span class="muted">No open positions</span>'

    trade_count = len(pf.get("trades", []))

    return f"""
    <div class="card" style="border-top:3px solid {COLORS.get(name,'#888')}">
        <h2>{name}</h2>
        <div class="big-value">${total:,.2f}</div>
        <div class="pnl {pc}">{sign}${pnl:,.2f} &nbsp;({sign}{pnl_pct:.2f}%)</div>
        <div class="meta">
            <span>Cash: ${cash:,.2f}</span>
            <span>Started: ${start:,.2f}</span>
            <span>Trades: {trade_count}</span>
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
    for t in all_trades[:80]:
        ts = t["time"][5:16].replace("T", " ")
        ac = "buy" if t["action"] == "BUY" else "sell"
        pnl_cell = ""
        if t["action"] == "SELL" and "trade_pnl" in t:
            p  = t["trade_pnl"]
            pc = "pos" if p >= 0 else "neg"
            pnl_cell = f'<span class="{pc}">{("+" if p >= 0 else "")}{p:.2f}</span>'
        reason = t.get("reason", "—")
        rows += f"""
        <tr>
            <td class="muted">{ts}</td>
            <td>{t['agent']}</td>
            <td><span class="{ac}">{t['action']}</span></td>
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
    labels = [s["time"][5:] for s in snapshots]
    datasets = []
    for name in AGENT_NAMES:
        datasets.append({
            "label": name,
            "data": [s.get(name) for s in snapshots],
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
    update_csv(portfolios)
    snapshots  = load_snapshots()

    cards_html  = "".join(build_agent_card(n, portfolios[n]) for n in AGENT_NAMES)
    trade_rows  = build_trade_rows(portfolios)
    chart_data  = build_chart_data(snapshots)
    updated     = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<title>Paper Trading Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:24px;max-width:1500px;margin:0 auto}}
  h1{{font-size:1.6rem;font-weight:700}}
  .subtitle{{color:#8b949e;font-size:.85rem;margin:6px 0 28px}}
  .cards{{display:flex;gap:14px;margin-bottom:28px;flex-wrap:wrap}}
  .card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:18px;flex:1;min-width:220px}}
  .card h2{{font-size:.8rem;color:#8b949e;margin-bottom:10px;text-transform:uppercase;letter-spacing:.05em}}
  .big-value{{font-size:1.8rem;font-weight:700;margin-bottom:4px}}
  .pnl{{font-size:.95rem;font-weight:600;margin-bottom:10px}}
  .pos{{color:#3fb950}}.neg{{color:#f85149}}
  .meta{{display:flex;gap:12px;font-size:.78rem;color:#8b949e;margin-bottom:10px;flex-wrap:wrap}}
  .positions{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
  .tag{{background:#21262d;border:1px solid #30363d;border-radius:4px;padding:2px 7px;font-size:.76rem}}
  .muted{{color:#8b949e}}
  .chart-box{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin-bottom:28px}}
  .chart-box h2{{font-size:.85rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:16px}}
  .section-title{{font-size:.85rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px}}
  .csv-note{{font-size:.8rem;color:#8b949e;margin-bottom:12px}}
  table{{width:100%;border-collapse:collapse;background:#161b22;border:1px solid #30363d;border-radius:10px;overflow:hidden;font-size:.82rem}}
  th{{background:#21262d;padding:10px 12px;text-align:left;font-size:.74rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}}
  td{{padding:9px 12px;border-top:1px solid #21262d;vertical-align:top}}
  .buy{{color:#3fb950;font-weight:700}}.sell{{color:#f85149;font-weight:700}}
  .reason-cell{{color:#8b949e;font-size:.77rem;max-width:400px;line-height:1.45}}
</style>
</head>
<body>
<h1>Paper Trading Dashboard</h1>
<p class="subtitle">
  Last updated: {updated} &nbsp;·&nbsp;
  Stock data delayed ~15 min (yfinance free tier) &nbsp;·&nbsp;
  Stop-loss: −8% &nbsp;·&nbsp; Take-profit: +15% &nbsp;·&nbsp;
  Page auto-refreshes every 10 min
</p>

<div class="cards">{cards_html}</div>

<div class="chart-box">
  <h2>Portfolio Value Over Time</h2>
  <canvas id="chart" height="60"></canvas>
</div>

<p class="section-title">Trade History &amp; Agent Reasoning</p>
<p class="csv-note">
  Full trade history also available as a spreadsheet:
  <a href="https://github.com/Gigantatoll/paper-trading/blob/main/data/trades.csv" style="color:#58a6ff">data/trades.csv</a>
  (updates automatically after every cycle)
</p>
<table>
  <thead>
    <tr>
      <th>Time (UTC)</th><th>Agent</th><th>Action</th><th>Stock</th>
      <th>Shares</th><th>Price</th><th>Total</th><th>Trade P&amp;L</th>
      <th>Why the agent did this</th>
    </tr>
  </thead>
  <tbody>{trade_rows}</tbody>
</table>

<script>
const cd={chart_data};
const ctx=document.getElementById('chart').getContext('2d');
new Chart(ctx,{{
  type:'line',
  data:{{labels:cd.labels,datasets:cd.datasets}},
  options:{{
    responsive:true,
    interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{labels:{{color:'#e6edf3',boxWidth:12}}}}}},
    scales:{{
      x:{{ticks:{{color:'#8b949e',maxTicksLimit:14}},grid:{{color:'#21262d'}}}},
      y:{{ticks:{{color:'#8b949e',callback:v=>'$'+v.toLocaleString()}},grid:{{color:'#21262d'}}}}
    }}
  }}
}});
</script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generated → {DOCS_DIR}/index.html")


if __name__ == "__main__":
    generate()
