"""Rich output helpers — panels, tables, colored response codes."""

import pyrad.packet
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

_CODE_STYLES = {
    pyrad.packet.AccessAccept: ("Access-Accept", "bold green"),
    pyrad.packet.AccessReject: ("Access-Reject", "bold red"),
    pyrad.packet.AccessChallenge: ("Access-Challenge", "bold yellow"),
    pyrad.packet.AccountingResponse: ("Accounting-Response", "bold green"),
}


def code_label(code: int) -> tuple[str, str]:
    """Return (label, rich style) for a RADIUS response code."""
    return _CODE_STYLES.get(code, (f"Unknown ({code})", "bold magenta"))


def connection_panel(server: str, port: int, secret: str) -> Panel:
    """Render a compact connection-info panel with masked secret."""
    masked = secret[:2] + "*" * (len(secret) - 2) if len(secret) > 2 else "***"
    content = f"[bold]{server}[/bold]:{port}  secret={masked}"
    return Panel(content, title="RADIUS Target", border_style="dim", expand=False)


def attribute_table(reply: pyrad.packet.Packet) -> Table | None:
    """Build a Rich Table of reply AVPs. Returns None if the reply has no attributes."""
    keys = list(reply.keys())
    if not keys:
        return None
    table = Table(title="Reply Attributes", show_header=True, header_style="bold cyan")
    table.add_column("Attribute", style="bold")
    table.add_column("Value")
    for key in sorted(keys):
        values = reply[key]
        for val in values:
            table.add_row(str(key), str(val))
    return table
