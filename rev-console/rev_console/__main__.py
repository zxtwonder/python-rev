#!/usr/bin/env python3
"""rev-console — Interactive CLI for REV Robotics Expansion Hubs."""

import asyncio
import sys

import click

from rev_expansion_hub import open_connected_expansion_hubs
from rev_hub_cli.__main__ import _get_expansion_hub
from rev_hub_cli.hub_stringify import hub_hierarchy_to_string
from rev_console.app import RevConsoleApp


def _run(coro):
    try:
        return asyncio.run(coro)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli() -> None:
    """rev-console — Interactive CLI for REV Robotics Expansion Hubs."""


@cli.command("list")
def cmd_list() -> None:
    """List all connected expansion hubs."""

    async def _go() -> None:
        hubs = await open_connected_expansion_hubs()
        if not hubs:
            click.echo("No hubs connected.")
            return
        for hub in hubs:
            click.echo(hub_hierarchy_to_string(hub))
        await asyncio.sleep(2)
        for hub in hubs:
            hub.close()

    _run(_go())


@cli.command("connect")
@click.option(
    "-s",
    "--serial",
    "serial_number",
    default=None,
    help="Serial number of the parent hub (starts with DQ)",
)
@click.option(
    "-p",
    "--parent",
    "parent_address",
    type=int,
    default=None,
    help="Module address of the parent hub",
)
@click.option(
    "-c",
    "--child",
    "child_address",
    type=int,
    default=None,
    help="Module address of a child hub (requires --parent)",
)
def cmd_connect(
    serial_number: str | None,
    parent_address: int | None,
    child_address: int | None,
) -> None:
    """Connect to a hub and enter interactive mode."""

    async def _go() -> None:
        hub, close = await _get_expansion_hub(
            serial_number, parent_address, child_address
        )
        try:
            await RevConsoleApp(hub).run_async()
        finally:
            close()

    _run(_go())


if __name__ == "__main__":
    cli()
