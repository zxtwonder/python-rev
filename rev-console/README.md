# rev-console

Interactive TUI console for REV Robotics Expansion Hubs, built with
[Textual](https://textual.textualize.io/).

## Requirements

- Python 3.12+
- `rev-hub-cli` (and its transitive dependencies: `rev-core`, `rev-rhsplib`,
  `rev-expansion-hub`, `rev-distance-sensor`)
- `textual >= 0.80`
- `click >= 8.0`
- A terminal with mouse and colour support (xterm, iTerm2, Windows Terminal, etc.)

## Install

Install all dependencies first (see [rev-rhsplib/README.md](../rev-rhsplib/README.md)
for C build requirements), then:

```sh
pip install ../rev-core
pip install ../rev-rhsplib
pip install ../rev-expansion-hub
pip install ../rev-distance-sensor
pip install ../rev-hub-cli
pip install .
```

This installs the `rev-console` command.

## Usage

```
rev-console COMMAND [ARGS]...

Commands:
  list     List all connected expansion hubs
  connect  Connect to a hub and enter interactive mode
```

### list

```sh
rev-console list
```

### connect

```sh
rev-console connect                                  # auto-detect single hub
rev-console connect --serial DQ123456 --parent 1     # by serial number
rev-console connect --parent 1                       # by module address
rev-console connect --parent 1 --child 2             # child hub
```

| Option | Description |
|---|---|
| `-s, --serial TEXT` | Serial number of the parent hub (starts with DQ) |
| `-p, --parent INT` | Module address of the parent hub |
| `-c, --child INT` | Module address of a child hub (requires `--parent`) |

## Interactive mode

The full-screen TUI shows a scrollable output log on the left and a collapsible
watch panel on the right. The hub connection (including the keep-alive task)
stays open for the entire session.

### Layout

```
┌────────────────────────────┬─────────────────┐
│ output log                 │ Watches         │
│                            │                 │
│ > watch add analog 0       │ [1] analog 0    │
│ Watch [1] started …        │     3 301 mV    │
│ > motor power 0 0.5        │                 │
│ Motor 0 at power 0.50. …   │ [2] temperature │
│ >                          │     25.3 °C     │
├────────────────────────────┴─────────────────┤
│ rev-hub> _                                   │
└──────────────────────────────────────────────┘
```

The watch panel is hidden when no watches are active and appears automatically
when the first watch is started.

### Key bindings

| Key | Action |
|---|---|
| **Ctrl+C** | Cancel the running `--continuous` command; return to prompt |
| **Ctrl+Q** | Quit and disconnect |
| **↑ / ↓** | Navigate command history |

Mouse clicks are supported — the **×** button on each watch widget closes it.

### Continuous mode

Add `--continuous` to stream readings to the output log. Press **Ctrl+C** to
stop and return to the prompt (the hub stays connected).

```
rev-hub> analog 0 --continuous
3300
3301
(stopped)
rev-hub>
```

### Watch panel

Use `watch add` to pin a live-refreshing value in the right panel. Optionally
set the refresh rate in Hz with `--rate` (default 1 Hz):

```
rev-hub> watch add analog 0
Watch [1] started: analog 0 at 1.0 Hz
rev-hub> watch add --rate 2 temperature
Watch [2] started: temperature at 2.0 Hz
rev-hub> watch list
[1] analog 0    (1.0 Hz / 1.00s)
[2] temperature (2.0 Hz / 0.50s)
rev-hub> watch close 1
Watch [1] closed.
```

Close a watch with `watch close <n>` or by clicking the **×** button on the
widget. Indices are stable — closing watch [1] does not renumber watch [2].

Only readable commands (those that accept `--continuous`) can be watched.

### Motor and servo commands

`motor power`, `motor velocity`, `motor position`, and `servo` start the
output and return to the prompt immediately. Stop them explicitly:

```
rev-hub> motor power 0 0.5
Motor 0 at power 0.50. Use 'motor disable 0' to stop.
rev-hub> motor disable 0
Motor 0 disabled.

rev-hub> servo 0 1500
Servo 0 running. Use 'servo disable 0' to stop.
rev-hub> servo disable 0
Servo 0 disabled.
```

`motor position` puts the hub in position-control mode and waits until the
encoder reaches the target, then returns to the prompt.

### Full command reference

| Command | Description |
|---|---|
| `analog <ch> [--continuous]` | Analog input (mV) |
| `temperature [--continuous]` | Hub temperature (°C) |
| `5vRailVoltage [--continuous]` | 5V rail voltage (mV) |
| `i2c-current [--continuous]` | I2C subsystem current (mA) |
| `digital-current [--continuous]` | Digital bus current (mA) |
| `servo-current [--continuous]` | Total servo current (mA) |
| `battery voltage [--continuous]` | Battery voltage (mV) |
| `battery current [--continuous]` | Battery current (mA) |
| `bulkInput [--continuous]` | All inputs at once (JSON) |
| `digital read <ch> [--continuous]` | Digital input pin |
| `digital readall [--continuous]` | All digital pins as bitfield |
| `digital write <ch> <high\|low\|1\|0>` | Write digital output pin |
| `digital writeall <bits> <mask>` | Write all pins (binary strings) |
| `motor power <ch> <power>` | Start motor at constant power [-1.0, 1.0] |
| `motor velocity <ch> <speed>` | Start motor at constant velocity (counts/s) |
| `motor position <ch> <vel> <pos> <tol>` | Move motor to encoder position (waits for completion) |
| `motor disable <ch>` | Disable motor |
| `motor encoder <ch> [-r] [--continuous]` | Encoder position; `-r` resets first |
| `motor current <ch> [--continuous]` | Motor current (mA) |
| `motor pid set <ch> <p> <i> <d>` | Set PID coefficients |
| `motor pid get <ch>` | Get PID/PIDF coefficients |
| `motor pidf set <ch> <p> <i> <d> <f>` | Set PIDF coefficients |
| `motor pidf get <ch>` | Get PIDF coefficients |
| `motor alert get <ch>` | Get motor alert threshold (mA) |
| `motor alert set <ch> <mA>` | Set motor alert threshold |
| `servo <ch> <pulse_width> [frame_width]` | Start servo (frame default 4000 µs) |
| `servo disable <ch>` | Disable servo |
| `distance <ch> [--continuous]` | Distance sensor (mm) |
| `version` | Firmware/hardware version |
| `led <r> <g> <b>` | Set LED color (0–255 each) |
| `get-led` | Get current LED color |
| `pattern <steps...>` | Set LED animation pattern |
| `get-pattern` | Get current LED pattern |
| `query <name>` | Query interface by name |
| `log <text>` | Inject data log hint (max 100 chars) |
| `loglevel <group> <level>` | Set debug log verbosity (0–3) |
| `failsafe` | Trigger fail-safe demonstration |
| `watch add [--rate <hz>] <command...>` | Pin a live-updating value in the watch panel |
| `watch list` | List active watches with indices |
| `watch close <n>` | Close watch by index |
| `help` | Show command reference |
| `exit` / `quit` | Disconnect and exit |

Command history (↑/↓) is persisted to `~/.rev_console_history`.

## Type checking

```sh
pip install -e ../rev-core \
            -e ../rev-rhsplib \
            -e ../rev-expansion-hub \
            -e ../rev-distance-sensor \
            -e ../rev-hub-cli \
            -e ".[dev]"
mypy rev_console/
```

## Lint

```sh
ruff check rev_console/
```
