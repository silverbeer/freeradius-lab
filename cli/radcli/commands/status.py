"""status — Server liveness check (Status-Server with auth probe fallback)."""

import time
from typing import Annotated

import pyrad.packet
import typer
from rich.console import Console

from radcli.client import make_client
from radcli.config import RadiusConfig
from radcli.display import connection_panel

console = Console()

# Status-Server code (RFC 5997) — not in all pyrad versions as a constant
STATUS_SERVER_CODE = 12


def status(
    ctx: typer.Context,
    probe_user: Annotated[
        str,
        typer.Option("--probe-user", help="Username for auth-probe fallback"),
    ] = "testrunner",
    probe_pass: Annotated[
        str,
        typer.Option("--probe-pass", help="Password for auth-probe fallback"),
    ] = "run123",
) -> None:
    """Check if the RADIUS server is alive (Status-Server with auth fallback)."""
    config: RadiusConfig = ctx.obj["config"]
    console.print(connection_panel(config.server, config.auth_port, config.secret))

    client = make_client(config)

    # Try Status-Server first
    with console.status("Sending Status-Server..."):
        try:
            req = client.CreateAuthPacket(code=STATUS_SERVER_CODE)
            req["NAS-Identifier"] = "radcli"
            start = time.monotonic()
            reply = client.SendPacket(req)
            latency_ms = (time.monotonic() - start) * 1000
            console.print(
                f"\n[bold green]Server alive[/] via Status-Server  "
                f"(code={reply.code}, {latency_ms:.0f} ms)"
            )
            raise typer.Exit(code=0)
        except typer.Exit:
            raise
        except Exception:
            console.print("[dim]Status-Server not supported, falling back to auth probe...[/]")

    # Fallback: send a real Access-Request
    with console.status("Sending auth probe..."):
        try:
            req = client.CreateAuthPacket(
                code=pyrad.packet.AccessRequest,
                User_Name=probe_user,
                NAS_Identifier="radcli",
            )
            req["User-Password"] = req.PwCrypt(probe_pass)
            start = time.monotonic()
            reply = client.SendPacket(req)
            latency_ms = (time.monotonic() - start) * 1000
            label = "Accept" if reply.code == pyrad.packet.AccessAccept else "Reject"
            console.print(
                f"\n[bold green]Server alive[/] via auth probe  "
                f"(Access-{label}, {latency_ms:.0f} ms)"
            )
            raise typer.Exit(code=0)
        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"\n[bold red]Server unreachable:[/] {exc}")
            raise typer.Exit(code=1)
