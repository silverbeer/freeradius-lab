"""authz — Auth + detailed attribute inspection with annotations."""

from typing import Annotated

import pyrad.packet
import typer
from rich.console import Console
from rich.table import Table

from radcli.client import make_client
from radcli.config import RadiusConfig
from radcli.display import code_label, connection_panel

console = Console()

# Known attribute descriptions for richer output
_ATTR_NOTES = {
    "Session-Timeout": "Max session duration (seconds)",
    "Reply-Message": "Server greeting / message to client",
    "Framed-Protocol": "L2 framing for the session",
    "Framed-IP-Address": "IP assigned to client",
    "Framed-IP-Netmask": "Subnet mask for client",
    "Idle-Timeout": "Max idle time before disconnect (seconds)",
    "Service-Type": "Type of service authorized",
    "Class": "Opaque value echoed in accounting",
}


def authz(
    ctx: typer.Context,
    user: Annotated[str, typer.Option("--user", "-u", help="Username")] = "testrunner",
    password: Annotated[str, typer.Option("--pass", "-p", help="Password")] = "run123",
) -> None:
    """Authenticate and show detailed reply attributes with annotations."""
    config: RadiusConfig = ctx.obj["config"]
    console.print(connection_panel(config.server, config.auth_port, config.secret))

    client = make_client(config)
    req = client.CreateAuthPacket(
        code=pyrad.packet.AccessRequest,
        User_Name=user,
        NAS_Identifier="radcli",
    )
    req["User-Password"] = req.PwCrypt(password)

    with console.status("Sending Access-Request..."):
        try:
            reply = client.SendPacket(req)
        except Exception as exc:
            console.print(f"[bold red]Error:[/] {exc}")
            raise typer.Exit(code=2)

    label, style = code_label(reply.code)
    console.print(f"\nResult: [{style}]{label}[/]  (user={user})")

    keys = list(reply.keys())
    if keys:
        table = Table(
            title="Authorization Attributes",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Attribute", style="bold")
        table.add_column("Value")
        table.add_column("Note", style="dim")

        for key in sorted(keys):
            values = reply[key]
            note = _ATTR_NOTES.get(str(key), "")
            for val in values:
                table.add_row(str(key), str(val), note)

        console.print(table)
    else:
        console.print("[dim]No reply attributes.[/]")

    if reply.code == pyrad.packet.AccessAccept:
        raise typer.Exit(code=0)
    raise typer.Exit(code=1)
