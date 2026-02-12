"""profile — List, inspect, and import named RADIUS server profiles."""

import json
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.table import Table

from radcli.config import load_profiles, get_profile, save_profile
from radcli.display import console

profile_app = typer.Typer(help="Manage named server profiles (profiles.toml).")


@profile_app.command(name="list")
def profile_list() -> None:
    """Show all available profiles."""
    profiles = load_profiles()
    if not profiles:
        console.print("[yellow]No profiles.toml found.[/]")
        console.print("  cp profiles.toml.example profiles.toml")
        raise typer.Exit(code=1)

    table = Table(title="Profiles", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Server")
    table.add_column("Auth Port")
    table.add_column("Acct Port")

    for name, cfg in profiles.items():
        table.add_row(
            name,
            cfg.get("server", "—"),
            str(cfg.get("auth_port", "—")),
            str(cfg.get("acct_port", "—")),
        )

    console.print(table)


@profile_app.command(name="show")
def profile_show(
    name: str = typer.Argument(help="Profile name to display"),
) -> None:
    """Show full details for a single profile (secret is masked)."""
    cfg = get_profile(name)

    secret = cfg.get("secret", "")
    if len(secret) > 2:
        masked = secret[:2] + "*" * (len(secret) - 2)
    else:
        masked = "***"

    console.print(f"\n[bold]Profile:[/] {name}")
    console.print(f"  server    = {cfg.get('server', '—')}")
    console.print(f"  secret    = {masked}")
    console.print(f"  auth_port = {cfg.get('auth_port', '—')}")
    console.print(f"  acct_port = {cfg.get('acct_port', '—')}")


@profile_app.command(name="import-tf")
def profile_import_tf(
    name: Annotated[
        str,
        typer.Argument(help="Profile name to create/update"),
    ] = "terraform",
    terraform_dir: Annotated[
        Optional[Path],
        typer.Option("--terraform-dir", "-d", help="Path to terraform directory"),
    ] = None,
    secret: Annotated[
        str,
        typer.Option("--secret", "-k", help="RADIUS shared secret"),
    ] = "testing123",
) -> None:
    """Import a profile from terraform output (radius_test_config)."""
    tf_dir = terraform_dir or Path.cwd().parent / "terraform"
    if not (tf_dir / ".terraform").exists():
        console.print(f"[bold red]Error:[/] no terraform state in {tf_dir}")
        console.print("  Run 'terraform init && terraform apply' first,")
        console.print("  or specify --terraform-dir.")
        raise typer.Exit(code=1)

    with console.status("Reading terraform output..."):
        try:
            result = subprocess.run(
                ["terraform", "output", "-raw", "radius_test_config"],
                cwd=tf_dir,
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            console.print("[bold red]Error:[/] terraform CLI not found on PATH")
            raise typer.Exit(code=1)
        except subprocess.CalledProcessError as exc:
            console.print(f"[bold red]Error:[/] terraform output failed")
            if exc.stderr:
                console.print(f"  {exc.stderr.strip()}")
            raise typer.Exit(code=1)

    try:
        tf_config = json.loads(result.stdout)
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/] could not parse radius_test_config as JSON")
        raise typer.Exit(code=1)

    profile = {
        "server": tf_config["server_ip"],
        "secret": secret,
        "auth_port": tf_config.get("auth_port", 1812),
        "acct_port": tf_config.get("acct_port", 1813),
    }

    path = save_profile(name, profile)
    console.print(f"[bold green]Imported[/] profile [bold]{name}[/] from terraform")
    console.print(f"  server    = {profile['server']}")
    console.print(f"  auth_port = {profile['auth_port']}")
    console.print(f"  acct_port = {profile['acct_port']}")
    console.print(f"  saved to  = {path}")
    console.print(f"\n  Use it:  radcli -P {name} status")
