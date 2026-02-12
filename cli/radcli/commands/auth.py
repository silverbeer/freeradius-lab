"""auth — Send Access-Request, show Accept/Reject."""

from typing import Annotated

import pyrad.packet
import typer
from rich.console import Console

from radcli.client import make_client
from radcli.config import RadiusConfig
from radcli.display import attribute_table, code_label, connection_panel

console = Console()


def auth(
    ctx: typer.Context,
    user: Annotated[str, typer.Option("--user", "-u", help="Username")] = "testrunner",
    password: Annotated[str, typer.Option("--pass", "-p", help="Password")] = "run123",
) -> None:
    """Send an Access-Request and display the result."""
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
    console.print(f"\nResult: [{style}]{label}[/]")

    table = attribute_table(reply)
    if table:
        console.print(table)

    if reply.code == pyrad.packet.AccessAccept:
        raise typer.Exit(code=0)
    raise typer.Exit(code=1)
