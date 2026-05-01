# rev-hub-cli

Command-line tool for interacting with REV Robotics Expansion Hubs.

## Requirements

- Python 3.12+
- `rev-core`, `rev-rhsplib`, `rev-expansion-hub`, `rev-distance-sensor`
- `click >= 8.0`

## Install

Install all dependencies in order, then this package:

```sh
pip install ../rev-core
pip install ../rev-rhsplib          # see rev-rhsplib/README.md for build requirements
pip install ../rev-expansion-hub
pip install ../rev-distance-sensor
pip install .
```

This installs the `rev-hub` command on your `PATH`.

## Type checking

```sh
pip install -e ../rev-core \
            -e ../rev-rhsplib \
            -e ../rev-expansion-hub \
            -e ../rev-distance-sensor \
            -e ".[dev]"
mypy rev_hub_cli/
```

## Compilation

Pure Python — no compilation step. Only `rev-rhsplib` (a transitive dependency)
requires compilation; see [rev-rhsplib/README.md](../rev-rhsplib/README.md).

## Usage

```
rev-hub [OPTIONS] COMMAND [ARGS]...

Options:
  -s, --serial TEXT    Serial number of the parent hub (starts with DQ)
  -p, --parent INT     Module address of the parent hub
  -c, --child INT      Module address of a child hub (requires --parent)
  --version            Show version and exit.
  --help               Show this message and exit.
```

When no `--serial` / `--parent` is given, the CLI auto-detects the single
connected hub. If multiple hubs are connected, `--serial` is required.

### Example commands

```sh
# List all connected hubs
rev-hub list

# Read firmware version
rev-hub version

# Set LED color (R G B, values 0-255)
rev-hub led 0 255 0

# Read analog input 0 continuously
rev-hub analog 0 --continuous

# Run motor 0 at 50% power
rev-hub motor power 0 0.5

# Read distance sensor on I2C channel 0
rev-hub distance 0

# Digital write
rev-hub digital write 0 high

# Servo on channel 0, 1500 µs pulse
rev-hub servo 0 1500

# Battery voltage
rev-hub battery voltage

# Specify a hub by serial number and parent address
rev-hub --serial DQ123456 --parent 1 version
```

### Full command list

| Command | Description |
|---|---|
| `list` | List all connected hubs and their children |
| `version` | Print firmware/hardware version |
| `led <r> <g> <b>` | Set onboard LED color |
| `get-led` | Get current LED color |
| `pattern <steps...>` | Set LED animation pattern (e.g. `100FF00 0.5FF0000`) |
| `get-pattern` | Get current LED pattern |
| `analog <port>` | Read analog input in mV |
| `temperature` | Read hub temperature in °C |
| `5vRailVoltage` | Read 5V rail voltage in mV |
| `battery voltage` | Read battery voltage in mV |
| `battery current` | Read battery current in mA |
| `i2c-current` | Read I2C subsystem current in mA |
| `digital-current` | Read digital bus current in mA |
| `servo-current` | Read total servo current in mA |
| `digital write <ch> <state>` | Write a digital pin (high/low/1/0) |
| `digital read <ch>` | Read a digital pin |
| `digital readall` | Read all digital pins as a bitfield |
| `digital writeall <bitfield> <bitmask>` | Write all digital pins |
| `motor power <ch> <power>` | Run motor at constant power [-1.0, 1.0] |
| `motor velocity <ch> <speed>` | Run motor at constant velocity (counts/s) |
| `motor position <ch> <vel> <pos> <tol>` | Run motor to position |
| `motor encoder <ch>` | Read encoder count (`-r` to reset) |
| `motor current <ch>` | Read motor current in mA |
| `motor pid set <ch> <p> <i> <d>` | Set PID coefficients |
| `motor pid get <ch>` | Get PID/PIDF coefficients |
| `motor pidf set <ch> <p> <i> <d> <f>` | Set PIDF coefficients |
| `motor pidf get <ch>` | Get PIDF coefficients |
| `motor alert get <ch>` | Get motor alert threshold in mA |
| `motor alert set <ch> <mA>` | Set motor alert threshold |
| `servo <ch> <pulse_width> [frame_width]` | Run a servo |
| `distance <ch>` | Read distance sensor in mm |
| `bulkInput` | Read all inputs at once |
| `query <name>` | Query interface information |
| `log <text>` | Inject a data log hint |
| `loglevel <group> <level>` | Set debug log verbosity (0–3) |
| `failsafe` | Trigger fail-safe demonstration |
| `testErrorHandling` | Demonstrate error handling |

Most commands accept `--continuous` to run in a loop.
