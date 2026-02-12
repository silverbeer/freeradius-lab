"""Typer app — global options and command registration."""

from typing import Annotated, Optional

import typer

from radcli.config import load_config

app = typer.Typer(
    name="radcli",
    help="Interactive CLI for ad-hoc FreeRADIUS testing.",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    profile: Annotated[
        Optional[str],
        typer.Option("--profile", "-P", help="Named profile from profiles.toml"),
    ] = None,
    server: Annotated[
        Optional[str],
        typer.Option("--server", "-s", help="RADIUS server address"),
    ] = None,
    secret: Annotated[
        Optional[str],
        typer.Option("--secret", "-k", help="RADIUS shared secret"),
    ] = None,
    auth_port: Annotated[
        Optional[int],
        typer.Option("--auth-port", help="RADIUS auth port"),
    ] = None,
    acct_port: Annotated[
        Optional[int],
        typer.Option("--acct-port", help="RADIUS accounting port"),
    ] = None,
) -> None:
    """Global connection options (override .env / environment variables)."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(
        profile=profile,
        server=server,
        secret=secret,
        auth_port=auth_port,
        acct_port=acct_port,
    )


# Register subcommands
from radcli.commands import auth, acct, authz, status  # noqa: E402
from radcli.commands.profile import profile_app  # noqa: E402

app.command(name="auth")(auth.auth)
app.command(name="acct")(acct.acct)
app.command(name="authz")(authz.authz)
app.command(name="status")(status.status)
app.add_typer(profile_app, name="profile")
