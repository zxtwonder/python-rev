"""Bulk input data command."""

from __future__ import annotations

import dataclasses
import json

from rev_core.expansion_hub import ExpansionHub


async def get_bulk_input_data(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        data = await hub.get_bulk_input_data()
        print(json.dumps(dataclasses.asdict(data)))
        if not continuous:
            break
