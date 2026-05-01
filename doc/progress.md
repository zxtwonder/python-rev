# Progress

## Status: Complete (all packages written)

### rev-core ✅
- All enums, dataclasses, DigitalState, ABCs, error hierarchy
- `rev_core/__init__.py` re-exports all public symbols

### rev-rhsplib ✅
- `src/_rev_rhsplib.cpp`: full pybind11 binding of librhsp
- `CMakeLists.txt`: builds librhsp + extension, outputs `.so` to `rev_rhsplib/`
- `pyproject.toml`: scikit-build-core backend
- `rev_rhsplib/_rev_rhsplib.pyi`: type stubs
- `rev_rhsplib/__init__.py`: async wrappers (`Serial`, `RevHub`, all error codes/enums)

### rev-expansion-hub ✅
- `rev_expansion_hub/errors/rhsp_lib_error.py`
- `rev_expansion_hub/internal/error_conversion.py`
- `rev_expansion_hub/internal/expansion_hub.py` (`ExpansionHubInternal`)
- `rev_expansion_hub/start_keep_alive.py`
- `rev_expansion_hub/open_rev_hub.py`
- `rev_expansion_hub/discovery.py`
- `rev_expansion_hub/__init__.py`

### rev-distance-sensor ✅
- `rev_distance_sensor/registers.py`
- `rev_distance_sensor/i2c_utils.py`
- `rev_distance_sensor/drivers/distance_sensor_driver.py`
- `rev_distance_sensor/drivers/vl53l0x.py`
- `rev_distance_sensor/distance_sensor.py`
- `rev_distance_sensor/__init__.py`

### rev-hub-cli ✅
- `rev_hub_cli/hub_stringify.py`
- `rev_hub_cli/command/analog.py`
- `rev_hub_cli/command/bulk_input.py`
- `rev_hub_cli/command/digital.py`
- `rev_hub_cli/command/distance.py`
- `rev_hub_cli/command/error.py`
- `rev_hub_cli/command/failsafe.py`
- `rev_hub_cli/command/firmware_version.py`
- `rev_hub_cli/command/led.py`
- `rev_hub_cli/command/log.py`
- `rev_hub_cli/command/motor.py`
- `rev_hub_cli/command/query.py`
- `rev_hub_cli/command/servo.py`
- `rev_hub_cli/__main__.py` (Click CLI entry point)

### doc ✅
- `doc/architecture.md`
- `doc/decisions.md`
- `doc/progress.md`

## Session fixes (2026-04-30 → 2026-05-01)

- **`ctx.obj` kwarg mismatch** — aligned `__main__.py` dict keys (`"serial_number"`,
  `"parent_address"`, `"child_address"`) to `_get_expansion_hub()` parameter names.
- **Motor/servo commands exited immediately** — added `_wait_for_sigint()` helper
  (asyncio Event + `loop.add_signal_handler`) so `motor power`, `motor velocity`,
  `motor position`, and `servo` block until Ctrl+C, then disable output and close.
- **`RhspLibNativeError` naming** — C-extension exception renamed from `RhspLibError`
  to avoid collision with `rev_expansion_hub.RhspLibError`.
- **`py::native_enum`** — confirmed C extension uses pybind11 ≥ 3.0 native enums
  (`IntEnum` subclasses); documented in architecture and decisions.
- **`from __future__ import annotations`** — removed from all 25 Python source
  files (unnecessary in Python 3.12; none had genuine forward references).
- **Docstring audit** — verified all docstrings in rev-rhsplib, rev-core,
  rev-expansion-hub, and rev-hub-cli against Node source and librhsp headers;
  no fabricated claims found.

## Known limitations / not yet done
- No automated tests
- rev-rhsplib build not validated (requires librhsp headers + C toolchain)
- `getI2CWriteStatus` in rev-expansion-hub is exposed via rev-rhsplib but not
  directly surfaced through the rev-core `ExpansionHub` ABC (not in original TS ABC)
