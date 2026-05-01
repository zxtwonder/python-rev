"""Utilities for formatting hub information as human-readable text."""

from typing import cast

from rev_core.rev_hub import ParentRevHub, RevHub


def hub_hierarchy_to_string(hub: RevHub) -> str:
    """Return a multi-line string describing *hub* and its children.

    :param hub: Any :class:`~rev_core.RevHub` instance.
    :returns: Human-readable hierarchy string.
    """
    serial_number_text = ""
    if hub.is_parent():
        serial_number_text = f"({cast(ParentRevHub, hub).serial_number})"

    result = f"RevHub {serial_number_text}: {hub.module_address}\n"

    if hub.is_parent():
        for child in cast(ParentRevHub, hub).children:
            result += f"\tRevHub: {child.module_address}\n"

    return result
