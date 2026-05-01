"""Data log and debug log-level commands."""

from __future__ import annotations

from rev_core.debug_group import DebugGroup
from rev_core.expansion_hub import ExpansionHub
from rev_core.verbosity_level import VerbosityLevel


async def inject_log(hub: ExpansionHub, hint: str) -> None:
    await hub.inject_data_log_hint(hint)


async def set_debug_log_level(hub: ExpansionHub, group: str, level: int) -> None:
    group_map = {g.name.lower(): g for g in DebugGroup}
    debug_group = group_map.get(group.lower())
    if debug_group is None:
        raise ValueError(f"{group!r} is not a valid DebugGroup")

    verbosity_levels = [
        VerbosityLevel.Off,
        VerbosityLevel.Level1,
        VerbosityLevel.Level2,
        VerbosityLevel.Level3,
    ]
    verbosity = verbosity_levels[level]
    await hub.set_debug_log_level(debug_group, verbosity)
