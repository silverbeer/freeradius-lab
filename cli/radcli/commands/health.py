"""health — Docker container health checks for freeradius-lab."""

import subprocess

import typer
from rich.console import Console
from rich.table import Table

console = Console()

CONTAINER = "freeradius-lab"


def _docker_exec(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command inside the freeradius-lab container."""
    return subprocess.run(
        ["docker", "exec", CONTAINER, *cmd],
        capture_output=True,
        text=True,
    )


def health(
    ctx: typer.Context,
) -> None:
    """Run health checks against the freeradius-lab Docker container."""
    table = Table(title="freeradius-lab health", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    all_passed = True

    # 1. Container running?
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", CONTAINER],
        capture_output=True,
        text=True,
    )
    running = result.returncode == 0 and result.stdout.strip() == "running"
    table.add_row(
        "Container",
        "[green]running[/]" if running else "[red]not running[/]",
        CONTAINER,
    )
    if not running:
        all_passed = False
        console.print(table)
        console.print("\n[bold red]Container is not running.[/] Start with: docker compose up -d")
        raise typer.Exit(code=1)

    # 2. radiusd -v (version)
    result = _docker_exec(["radiusd", "-v"])
    if result.returncode == 0:
        version_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "unknown"
        table.add_row("Version", "[green]ok[/]", version_line)
    else:
        all_passed = False
        table.add_row("Version", "[red]fail[/]", result.stderr.strip()[:80])

    # 3. radiusd -C (config syntax)
    result = _docker_exec(["radiusd", "-C"])
    if result.returncode == 0:
        table.add_row("Config", "[green]valid[/]", "radiusd -C passed")
    else:
        all_passed = False
        detail = (result.stderr.strip() or result.stdout.strip())[:80]
        table.add_row("Config", "[red]invalid[/]", detail)

    # 4. Port bindings (check from host via docker port)
    for port in ["1812/udp", "1813/udp", "18121/udp"]:
        result = subprocess.run(
            ["docker", "port", CONTAINER, port],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            binding = result.stdout.strip().splitlines()[0]
            table.add_row(f"Port {port}", "[green]mapped[/]", binding)
        else:
            all_passed = False
            table.add_row(f"Port {port}", "[red]not mapped[/]", "")

    console.print(table)

    if all_passed:
        console.print("\n[bold green]All checks passed.[/]")
    else:
        console.print("\n[bold yellow]Some checks failed.[/]")
        raise typer.Exit(code=1)
