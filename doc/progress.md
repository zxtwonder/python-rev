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

## Known limitations / not yet done
- No automated tests
- rev-rhsplib build not validated (requires librhsp headers + C toolchain)
- `getI2CWriteStatus` in rev-expansion-hub is exposed via rev-rhsplib but not
  directly surfaced through the rev-core `ExpansionHub` ABC (not in original TS ABC)
