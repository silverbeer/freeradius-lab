"""pyrad Client factory — mirrors the radius_client fixture from tests/conftest.py."""

from pathlib import Path

import typer
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from rich.console import Console

from radcli.config import RadiusConfig

_console = Console(stderr=True)


def _find_dictionary() -> str:
    """Locate the RADIUS dictionary file, checking common locations."""
    candidates = [
        Path.cwd() / "dictionary",                      # run from cli/
        Path.cwd() / "cli" / "dictionary",               # run from repo root
        Path.cwd() / "tests" / "dictionary",             # run from repo root (direct)
        Path(__file__).resolve().parent.parent / "dictionary",  # relative to source
    ]
    for path in candidates:
        resolved = path.resolve()
        if resolved.exists():
            return str(resolved)

    # Fall back to pyrad's bundled example dictionary
    import pyrad
    bundled = Path(pyrad.__file__).resolve().parent.parent / "example" / "dictionary"
    if bundled.exists():
        return str(bundled)

    return ""


def make_client(config: RadiusConfig) -> Client:
    """Create a pyrad Client from the given config."""
    dict_path = _find_dictionary()
    if not dict_path:
        _console.print(
            "[bold red]Error:[/] RADIUS dictionary not found.\n"
            "  Run radcli from the cli/ or repo root directory,\n"
            "  or ensure the dictionary symlink exists."
        )
        raise typer.Exit(code=1)
    client = Client(
        server=config.server,
        secret=config.secret.encode(),
        dict=Dictionary(dict_path),
        authport=config.auth_port,
        acctport=config.acct_port,
    )
    client.retries = 3
    client.timeout = 5
    return client
