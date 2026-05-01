"""Distance sensor command."""

from __future__ import annotations

from rev_core.expansion_hub import ExpansionHub
from rev_distance_sensor import DistanceSensor


async def distance(hub: ExpansionHub, channel: int, continuous: bool) -> None:
    sensor = DistanceSensor(hub, channel)
    await sensor.setup()

    if continuous:
        sensor.start_measuring_distance(
            lambda mm: print(f"Distance is {mm}mm"), 1.0
        )
    else:
        mm = await sensor.get_distance_millimeters()
        print(f"Distance is {mm}mm")
        sensor.stop()
        hub.close()
