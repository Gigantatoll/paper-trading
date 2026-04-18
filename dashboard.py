from datetime import datetime

import pytz
from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class Dashboard:
    def __init__(self, agents, market_data):
        self.agents = agents
        self.market_data = market_data
        self.next_update_in: int = 0

    # ------------------------------------------------------------------ #

    def render(self):
        return Group(
            self._header(),
            Columns([self._agent_panel(a) for a in self.agents], equal=True, expand=True),
            self._trades_panel(),
        )

    # ------------------------------------------------------------------ #

    def _header(self) -> Panel:
        ny = pytz.timezone("America/New_York")
        now = datetime.now(ny)
        open_ = self.market_data.is_market_open()
        status_tag = "[bold green]OPEN[/bold green]" if open_ else "[bold red]CLOSED[/bold red]"
        updated = (
            self.market_data.last_updated.strftime("%H:%M:%S")
            if self.market_data.last_updated
            else "—"
        )
        return Panel(
            f"  [bold white]Paper Trading System[/bold white]   "
            f"Market: {status_tag}   "
            f"NY Time: [cyan]{now.strftime('%H:%M:%S')}[/cyan]   "
            f"Data status: [yellow]{self.market_data.status}[/yellow]   "
            f"Last fetch: [dim]{updated}[/dim]   "
            f"Next cycle in: [bold]{self.next_update_in}s[/bold]",
            style="on grey15",
            padding=(0, 1),
        )

    def _agent_panel(self, agent) -> Panel:
        prices = self.market_data.current_prices
        pf = agent.portfolio

        tv = pf.total_value(prices)
        pnl = pf.pnl(prices)
        pnl_pct = pf.pnl_pct(prices)
        color = "green" if pnl >= 0 else "red"
        sign = "+" if pnl >= 0 else ""

        # ── summary grid ──────────────────────────────────────────────
        grid = Table.grid(padding=(0, 2))
        grid.add_row(
            Text("Value", style="dim"),
            Text(f"${tv:,.2f}", style="bold white"),
            Text("Cash", style="dim"),
            Text(f"${pf.cash:,.2f}", style="white"),
        )
        grid.add_row(
            Text("P&L", style="dim"),
            Text(f"{sign}${pnl:,.2f}  ({sign}{pnl_pct:.2f}%)", style=f"bold {color}"),
            Text("Positions", style="dim"),
            Text(str(len(pf.positions)), style="white"),
        )

        # ── positions table ───────────────────────────────────────────
        tbl = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold dim",
            padding=(0, 1),
            expand=True,
        )
        tbl.add_column("Ticker", style="cyan bold")
        tbl.add_column("Shares", justify="right")
        tbl.add_column("Entry", justify="right")
        tbl.add_column("Price", justify="right")
        tbl.add_column("P&L", justify="right")

        for symbol, pos in pf.positions.items():
            cur = prices.get(symbol, pos["avg_price"])
            pos_pnl = (cur - pos["avg_price"]) * pos["shares"]
            c = "green" if pos_pnl >= 0 else "red"
            tbl.add_row(
                symbol,
                str(int(pos["shares"])),
                f"${pos['avg_price']:.2f}",
                f"${cur:.2f}",
                f"[{c}]{'+' if pos_pnl >= 0 else ''}{pos_pnl:.2f}[/{c}]",
            )

        if not pf.positions:
            tbl.add_row("[dim]—[/dim]", "—", "—", "—", "—")

        last = Text(agent.last_action or "Waiting for first cycle…", style="dim italic")
        err = Text(f"Error: {agent.last_error}", style="red") if agent.last_error else Text("")

        return Panel(
            Group(grid, Text(""), tbl, last, err),
            title=f"[bold]{agent.name}[/bold]",
            border_style="blue",
            padding=(1, 1),
        )

    def _trades_panel(self) -> Panel:
        all_trades = []
        for agent in self.agents:
            for trade in agent.portfolio.trades:
                all_trades.append((trade, agent.name))

        all_trades.sort(key=lambda x: x[0]["time"], reverse=True)
        all_trades = all_trades[:20]

        tbl = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold dim",
            expand=True,
            padding=(0, 1),
        )
        tbl.add_column("Time", style="dim", width=6)
        tbl.add_column("Agent", width=16)
        tbl.add_column("Action", width=6)
        tbl.add_column("Symbol", style="cyan bold", width=6)
        tbl.add_column("Shares", justify="right", width=7)
        tbl.add_column("Price", justify="right", width=9)
        tbl.add_column("Total", justify="right", width=11)

        for trade, agent_name in all_trades:
            c = "green" if trade["action"] == "BUY" else "red"
            tbl.add_row(
                trade["time"][11:16],
                agent_name,
                f"[{c}]{trade['action']}[/{c}]",
                trade["symbol"],
                str(int(trade["shares"])),
                f"${trade['price']:.2f}",
                f"${trade['total']:,.2f}",
            )

        if not all_trades:
            tbl.add_row("—", "—", "—", "—", "—", "—", "—")

        return Panel(tbl, title="[bold]Trade History[/bold]", border_style="dim", padding=(0, 1))
