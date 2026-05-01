# rev-expansion-hub

High-level asyncio API for REV Robotics Expansion Hubs.

## Requirements

- Python 3.12+
- `rev-core`
- `rev-rhsplib` (requires a working C++ build — see [rev-rhsplib/README.md](../rev-rhsplib/README.md))
- `pyserial >= 3.5`
- **Linux / macOS**: FTDI VCP driver is included in the kernel
- **Windows**: Install the [FTDI VCP driver](https://ftdi.com/drivers) so the hub
  appears as a COM port

## Install

Install dependencies in order, then this package:

```sh
pip install ../rev-core
pip install ../rev-rhsplib     # must be built first; see its README
pip install .
```

Or all at once from the repo root if using a tool that resolves local paths:

```sh
pip install -e ../rev-core -e ../rev-rhsplib -e .
```

For development:

```sh
pip install -e ".[dev]"
```

## Type checking

All upstream packages must be installed so mypy can resolve their types.
The C extension is typed via `rev_rhsplib/_rev_rhsplib.pyi` — it does not need
to be compiled to run the type checker.

```sh
pip install -e ../rev-core -e ../rev-rhsplib -e ".[dev]"
mypy rev_expansion_hub/
```

## Lint

```sh
ruff check rev_expansion_hub/
```

## Compilation

This is a pure Python package — no compilation step. Only `rev-rhsplib` (a
dependency) requires compilation; see [rev-rhsplib/README.md](../rev-rhsplib/README.md).

## Quick start

```python
import asyncio
from rev_expansion_hub import open_connected_expansion_hubs

async def main():
    hubs = await open_connected_expansion_hubs()
    hub = hubs[0]
    print(await hub.read_version_string())
    hub.close()

asyncio.run(main())
```
