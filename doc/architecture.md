# Architecture

## Package Overview

```
python-rev/
├── rev-core/               Pure Python — types, ABCs, error hierarchy
├── rev-rhsplib/            C++17 pybind11 extension linking librhsp
├── rev-expansion-hub/      asyncio implementation of the ExpansionHub ABC
├── rev-distance-sensor/    VL53L0X I2C driver over ExpansionHub
└── rev-hub-cli/            Click-based CLI (maps to node-rhsplib packages/sample)
```

## Dependency Graph

```
rev-hub-cli
    ├── rev-expansion-hub
    │       ├── rev-core
    │       └── rev-rhsplib
    │               └── rev-core
    └── rev-distance-sensor
            ├── rev-core
            └── rev-expansion-hub
```

## rev-core

Contains only pure Python:

- **Enums** (`IntEnum`): `RevHubType`, `MotorMode`, `DigitalChannelDirection`,
  `I2CSpeedCode`, `ClosedLoopControlAlgorithm`, `DebugGroup`, `VerbosityLevel`,
  `NackCode`
- **Dataclasses**: `BulkInputData`, `DiscoveredAddresses`, `I2CReadStatus`,
  `I2CWriteStatus`, `LedPattern`, `ModuleInterface`, `ModuleStatus`,
  `PidCoefficients`, `PidfCoefficients`, `Rgb`, `Version`
- **Special types**: `DigitalState` (singleton HIGH/LOW, not an enum)
- **ABCs**: `RevHub`, `ParentRevHub`, `ExpansionHub`, `ParentExpansionHub`
- **Errors**: `RevHubError` hierarchy (general + NACK-specific)

## rev-rhsplib

C++ pybind11 extension (`_rev_rhsplib.so`) + Python async wrappers:

- **Build**: scikit-build-core + CMake; librhsp compiled as a static library
- **C++ classes**: `PySerial` (wraps `RhspSerial`), `PyRevHub` (wraps `RhspRevHub`)
- **GIL**: Released around all blocking librhsp calls with `py::gil_scoped_release`
- **Exception**: `RhspLibException` in C++ → Python `RhspLibError` (with `error_code`
  and optional `nack_code` attributes) via `PyErr_SetObject`
- **Python wrapper**: `Serial` and `RevHub` classes with `asyncio.Lock` per hub,
  all I/O methods run in the default thread-pool executor via `run_in_executor`

## rev-expansion-hub

- **`ExpansionHubInternal`**: Implements `ExpansionHub` ABC using rev-rhsplib
- **Error conversion** (`internal/error_conversion.py`): Maps `RhspLibError` codes
  to typed rev-core exceptions
- **Keep-alive**: `asyncio.Task` loop calling `send_keep_alive()` every 1 second;
  background errors delivered to `on("error", ...)` listeners
- **Serial port registry**: Module-level `_open_serial_map` prevents double-opens
- **Discovery**: pyserial `list_ports.comports()` filtered by FTDI VID 0x0403,
  PID 0x6015, serial number prefix "DQ"

## rev-distance-sensor

- **`DistanceSensor`**: Thin facade over `DistanceSensorDriver` ABC
- **`VL53L0X`**: Full port of the ST VL53L0X Time-of-Flight driver; connects over
  I2C channel on the expansion hub (default address 0x29)
- **I2C utilities** (`i2c_utils.py`): `read_register`, `write_register`,
  `read_short`, `write_short`, `write_int` helpers

## rev-hub-cli

- **Entry point**: `rev_hub_cli.__main__:cli` (Click group)
- **Hub selection**: `--serial`, `--parent`, `--child` options; defaults to the
  single detected hub when no options are given
- **Command modules** (`command/`): one file per feature area, each exporting
  plain async functions called by Click actions via `asyncio.run()`

## asyncio Design

All hub I/O is `async def`. Blocking C calls run in the default thread-pool
executor. A per-hub `asyncio.Lock` inside rev-rhsplib serializes concurrent
coroutines to prevent interleaved serial frames. The keep-alive loop runs as a
background `asyncio.Task`.

## Windows Support

- pyserial handles COM port names transparently
- librhsp ships `win/serial.c` and `win/time.c` for Windows serial/timing
- FTDI Virtual COM Port (VCP) driver required on the host
- No pyusb dependency — all enumeration goes through pyserial
- `run_in_executor` makes blocking serial I/O non-blocking on all platforms
