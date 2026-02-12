"""Configuration loading: profiles.toml → .env file → environment variables → CLI overrides."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os


@dataclass
class RadiusConfig:
    server: str
    secret: str
    auth_port: int
    acct_port: int


def _profiles_path() -> Path:
    """Return the path to profiles.toml in the cli/ directory."""
    return Path.cwd() / "profiles.toml"


def load_profiles() -> dict[str, dict]:
    """Load all profiles from profiles.toml. Returns empty dict if file missing."""
    path = _profiles_path()
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_profile(name: str) -> dict:
    """Load a single profile by name. Raises typer.Exit on error."""
    import typer
    from radcli.display import console

    profiles = load_profiles()
    if not profiles:
        console.print(f"[bold red]Error:[/] profiles.toml not found in {Path.cwd()}")
        console.print("  cp profiles.toml.example profiles.toml")
        raise typer.Exit(code=1)
    if name not in profiles:
        available = ", ".join(profiles.keys())
        console.print(f"[bold red]Error:[/] profile [bold]{name}[/] not found")
        console.print(f"  Available: {available}")
        raise typer.Exit(code=1)
    return profiles[name]


def save_profile(name: str, profile: dict) -> Path:
    """Write or update a single profile in profiles.toml. Returns the file path."""
    path = _profiles_path()
    profiles = load_profiles()
    profiles[name] = profile

    lines: list[str] = []
    for section, values in profiles.items():
        if lines:
            lines.append("")
        lines.append(f"[{section}]")
        for key, val in values.items():
            if isinstance(val, str):
                lines.append(f'{key} = "{val}"')
            else:
                lines.append(f"{key} = {val}")

    path.write_text("\n".join(lines) + "\n")
    return path


def load_config(
    *,
    profile: str | None = None,
    server: str | None = None,
    secret: str | None = None,
    auth_port: int | None = None,
    acct_port: int | None = None,
) -> RadiusConfig:
    """Build config with precedence: CLI flags > .env/env vars > profile > defaults."""
    # Load .env from cli/ directory (where radcli is run)
    load_dotenv(Path.cwd() / ".env")

    # Start with defaults
    cfg_server = "localhost"
    cfg_secret = "testing123"
    cfg_auth_port = 1812
    cfg_acct_port = 1813

    # Layer 2: profile values (if selected)
    if profile:
        p = get_profile(profile)
        cfg_server = p.get("server", cfg_server)
        cfg_secret = p.get("secret", cfg_secret)
        cfg_auth_port = p.get("auth_port", cfg_auth_port)
        cfg_acct_port = p.get("acct_port", cfg_acct_port)

    # Layer 3: environment variables override profile
    cfg_server = os.environ.get("RADIUS_SERVER", cfg_server)
    cfg_secret = os.environ.get("RADIUS_SECRET", cfg_secret)
    cfg_auth_port = int(os.environ.get("RADIUS_AUTH_PORT", cfg_auth_port))
    cfg_acct_port = int(os.environ.get("RADIUS_ACCT_PORT", cfg_acct_port))

    # Layer 4: explicit CLI flags override everything
    return RadiusConfig(
        server=server or cfg_server,
        secret=secret or cfg_secret,
        auth_port=auth_port or cfg_auth_port,
        acct_port=acct_port or cfg_acct_port,
    )
