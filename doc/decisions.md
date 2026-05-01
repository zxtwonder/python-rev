# Key Decisions

## D-001: pybind11 for C++ binding

**Decision**: Use pybind11 (≥2.12) instead of ctypes or cffi.

**Reason**: pybind11 offers first-class GIL management (`py::gil_scoped_release`),
type-safe exception translation, and clean integration with CMake/scikit-build-core.

## D-002: scikit-build-core + CMake

**Decision**: Use scikit-build-core as the PEP 517 build backend for rev-rhsplib.

**Reason**: The closest match to librhsp's existing CMake build system.
scikit-build-core replaces the older scikit-build and supports PEP 517/518.

## D-003: asyncio with run_in_executor

**Decision**: Wrap all blocking C calls in `loop.run_in_executor(None, fn, *args)`.

**Reason**: librhsp performs synchronous serial I/O that can block for tens of
milliseconds. Running it in the thread-pool executor keeps the event loop responsive.

## D-004: Per-hub asyncio.Lock

**Decision**: Each `RevHub` instance in rev-rhsplib holds an `asyncio.Lock` that
is acquired around every hub operation.

**Reason**: Prevents interleaved serial frames when multiple coroutines concurrently
call methods on the same hub object.

## D-005: pyserial only (no pyusb)

**Decision**: Use `serial.tools.list_ports.comports()` for device enumeration; no
pyusb dependency.

**Reason**: On Windows the FTDI VCP driver presents the hub as a standard COM port.
pyserial can enumerate VID/PID/serial-number from the OS device list without raw
USB access. pyusb requires WinUSB/libusb which conflicts with the VCP driver.

## D-006: Error hierarchy mirrors rev-core

**Decision**: `RhspLibError` in rev-expansion-hub extends `RevHubError` (from
rev-core), not the `RhspLibError` from rev-rhsplib.

**Reason**: The C-extension `RhspLibError` is a low-level transport error. The
expansion-hub layer wraps it and converts to semantic rev-core errors; uncategorised
errors become `rev_expansion_hub.RhspLibError` (a `RevHubError`).

## D-007: I2C polling loop bug fix

**Decision**: Correct the TypeScript I2C polling bug in the Python port.

**Original bug**: The TS code uses `e! instanceof I2cOperationInProgressError` where
`!` is a TypeScript non-null assertion (not negation). The condition is therefore
`if (e instanceof I2cOperationInProgressError) throw e`, which exits the loop on
in-progress instead of continuing.

**Python fix**: Catch `I2cOperationInProgressError` and `continue`; re-raise all
other exceptions.

## D-008: Keep-alive as asyncio.Task

**Decision**: Use `asyncio.Task` instead of a thread or `setInterval` equivalent.

**Reason**: Stays entirely within asyncio; cancellation is clean via `task.cancel()`.
Background errors are surfaced to `on("error", ...)` listeners.

## D-009: DigitalState as non-enum class

**Decision**: Port TypeScript `DigitalState` as a plain class with singleton
class attributes `HIGH` and `LOW`, not as `IntEnum`.

**Reason**: The TypeScript original is a class, not an enum. `DigitalState` encodes
a boolean and has methods (`is_high()`, `is_low()`, `__bool__`).

## D-010: IntEnum for all protocol enums

**Decision**: All protocol enums use `IntEnum` so their numeric values are preserved.

**Reason**: librhsp functions take integer values mandated by the REV Hub Serial
Protocol spec. `IntEnum` lets Python code use readable names while passing the
correct numeric values to the C layer.

## D-011: LedPattern stores packed RGBT uint32 values

**Decision**: `LedPattern` stores 16 `rgbt_pattern_stepN: int` fields matching
the packed wire format.

**Reason**: The C library operates on 16 packed 32-bit integers. The higher-level
`create_led_pattern(steps)` function handles the packing for user convenience.
