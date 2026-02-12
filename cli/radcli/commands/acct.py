"""acct — Send Accounting-Request (Start/Stop/Interim)."""

import uuid
from typing import Annotated

import pyrad.packet
import typer
from rich.console import Console

from radcli.client import make_client
from radcli.config import RadiusConfig
from radcli.display import code_label, connection_panel

console = Console()

_STATUS_TYPES = {"start": "Start", "stop": "Stop", "interim": "Interim-Update"}


def acct(
    ctx: typer.Context,
    status_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Acct-Status-Type: start, stop, or interim"),
    ] = "start",
    user: Annotated[str, typer.Option("--user", "-u", help="Username")] = "testrunner",
    session_id: Annotated[
        str | None,
        typer.Option("--session-id", help="Acct-Session-Id (auto-generated if omitted)"),
    ] = None,
    session_time: Annotated[
        int | None,
        typer.Option("--session-time", help="Acct-Session-Time in seconds"),
    ] = None,
) -> None:
    """Send an Accounting-Request and display the result."""
    config: RadiusConfig = ctx.obj["config"]
    console.print(connection_panel(config.server, config.acct_port, config.secret))

    resolved_type = _STATUS_TYPES.get(status_type.lower())
    if resolved_type is None:
        console.print(f"[bold red]Invalid --type:[/] {status_type!r}  (use start, stop, or interim)")
        raise typer.Exit(code=2)

    sid = session_id or uuid.uuid4().hex[:16]
    console.print(f"[dim]Session-Id: {sid}  Status-Type: {resolved_type}[/]")

    client = make_client(config)
    req = client.CreateAcctPacket(code=pyrad.packet.AccountingRequest)
    req["User-Name"] = user
    req["Acct-Session-Id"] = sid
    req["Acct-Status-Type"] = resolved_type
    req["NAS-Identifier"] = "radcli"
    req["NAS-IP-Address"] = "127.0.0.1"

    if session_time is not None:
        req["Acct-Session-Time"] = session_time

    with console.status("Sending Accounting-Request..."):
        try:
            reply = client.SendPacket(req)
        except Exception as exc:
            console.print(f"[bold red]Error:[/] {exc}")
            raise typer.Exit(code=2)

    label, style = code_label(reply.code)
    console.print(f"\nResult: [{style}]{label}[/]")
    raise typer.Exit(code=0)
