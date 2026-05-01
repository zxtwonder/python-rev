"""Fail-safe demonstration command."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from rev_core.expansion_hub import ExpansionHub
from rev_hub_cli.command.servo import run_servo


async def send_fail_safe(hub: ExpansionHub, close: Callable[[], None]) -> None:
    """Start servo 0 for 2 seconds, send fail-safe, then close after 2 more seconds."""
    await run_servo(hub, 0, 1000, 4000)
    await asyncio.sleep(2)
    await hub.send_fail_safe()
    await asyncio.sleep(2)
    close()
