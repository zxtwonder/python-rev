"""Utilities for formatting hub information as human-readable text."""

from __future__ import annotations

from rev_core.rev_hub import RevHub


def hub_hierarchy_to_string(hub: RevHub) -> str:
    """Return a multi-line string describing *hub* and its children.

    :param hub: Any :class:`~rev_core.RevHub` instance.
    :returns: Human-readable hierarchy string.
    """
    serial_text = f"({hub.serial_number})" if hub.is_parent() else ""
    result = f"RevHub {serial_text}: {hub.module_address}\n"

    if hub.is_parent():
        for child in hub.children:
            result += f"\tRevHub: {child.module_address}\n"

    return result
