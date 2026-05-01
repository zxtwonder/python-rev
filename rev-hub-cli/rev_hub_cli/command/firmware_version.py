"""Firmware version command."""

from __future__ import annotations

from rev_core.expansion_hub import ExpansionHub


async def firmware_version(hub: ExpansionHub) -> None:
    version = await hub.read_version_string()
    print(f"Version is {version}")
