# rev-distance-sensor

Asyncio driver for the REV 2m Distance Sensor (VL53L0X) connected over I2C
to a REV Expansion Hub.

## Requirements

- Python 3.12+
- `rev-core`
- `rev-expansion-hub` (and its transitive dependency `rev-rhsplib`)

## Install

```sh
pip install ../rev-core
pip install ../rev-rhsplib     # see rev-rhsplib/README.md for build requirements
pip install ../rev-expansion-hub
pip install .
```

## Type checking

```sh
pip install -e ../rev-core -e ../rev-rhsplib -e ../rev-expansion-hub -e ".[dev]"
mypy rev_distance_sensor/
```

## Lint

```sh
ruff check rev_distance_sensor/
```

## Compilation

Pure Python — no compilation step. Only `rev-rhsplib` (a transitive dependency)
requires compilation; see [rev-rhsplib/README.md](../rev-rhsplib/README.md).

## Quick start

```python
import asyncio
from rev_expansion_hub import open_connected_expansion_hubs
from rev_distance_sensor import DistanceSensor

async def main():
    hubs = await open_connected_expansion_hubs()
    hub = hubs[0]

    sensor = DistanceSensor(hub, channel=0)
    await sensor.setup()

    distance_mm = await sensor.get_distance_millimeters()
    print(f"Distance: {distance_mm} mm")

    hub.close()

asyncio.run(main())
```
