"""Command objects and dispatch mixin for RevConsoleApp."""

import dataclasses
import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from rev_core.digital_state import DigitalState
from rev_core.expansion_hub import ExpansionHub
from rev_hub_cli.command.digital import digital_write, digital_write_all
from rev_hub_cli.command.failsafe import send_fail_safe
from rev_hub_cli.command.firmware_version import firmware_version
from rev_hub_cli.command.led import get_led, get_led_pattern, led, led_pattern
from rev_hub_cli.command.log import inject_log, set_debug_log_level
from rev_hub_cli.command.motor import (
    get_motor_alert_level_ma,
    get_motor_regulated_velocity_pidf,
    reset_encoder,
    run_motor_constant_power,
    run_motor_constant_velocity,
    run_motor_to_position,
    set_motor_alert_level,
    set_motor_regulated_velocity_pid,
    set_motor_regulated_velocity_pidf,
)
from rev_hub_cli.command.query import query_interface
from rev_hub_cli.command.servo import run_servo

CommandCallable = Callable[[], Coroutine[Any, Any, str]]


# ── CommandAction ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CommandAction:
    """Result of parsing a command token list.

    valid=False, error=""  → dispatcher shows the owning Command's help_text.
    valid=False, error=str → dispatcher shows the error reason instead.
    watchable → call() returns str; the command supports watch-panel reading.
    Continuous commands set watchable=False and a looping call() that runs
    until cancelled (CancelledError).
    """

    valid: bool
    watchable: bool
    call: CommandCallable | None  # None only when valid=False
    error: str = ""


def _create_valid_action(call: CommandCallable) -> CommandAction:
    return CommandAction(valid=True, watchable=False, call=call)


def _create_error_action(error: str) -> CommandAction:
    return CommandAction(valid=False, watchable=False, call=None, error=error)


def _create_read_action(read: CommandCallable, continuous: bool) -> CommandAction:
    """Wrap a one-shot reader into a CommandAction; build a loop if continuous=True."""
    if not continuous:
        return CommandAction(valid=True, watchable=True, call=read)

    async def _loop() -> str:  # type: ignore[return]
        while True:
            print(await read())

    return CommandAction(valid=True, watchable=False, call=_loop)


def _parse_flag(rest: list[str], flag: str) -> tuple[bool, list[str]]:
    found = flag in rest
    return found, [a for a in rest if a != flag]


def _parse_continuous_flag(rest: list[str]) -> tuple[bool, list[str]]:
    return _parse_flag(rest, "--continuous")


# ── Command base ──────────────────────────────────────────────────────────────


class Command(ABC):
    help_text: str = ""

    @abstractmethod
    def parse(self, rest: list[str]) -> CommandAction: ...


# ── No-argument readable commands ─────────────────────────────────────────────


class _NoArgRead(Command):
    """Base for zero-argument hub reads."""

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )
        return _create_read_action(self._read, continuous)

    @abstractmethod
    async def _read(self) -> str: ...


class TemperatureCommand(_NoArgRead):
    help_text = "temperature [--continuous]            Hub internal temperature (°C)"

    async def _read(self) -> str:
        return str(await self._hub.get_temperature())


class Voltage5vCommand(_NoArgRead):
    help_text = "5vRailVoltage [--continuous]           5 V rail voltage (mV)"

    async def _read(self) -> str:
        return str(await self._hub.get_5v_bus_voltage())


class I2cCurrentCommand(_NoArgRead):
    help_text = "i2c-current [--continuous]             I²C subsystem current (mA)"

    async def _read(self) -> str:
        return str(await self._hub.get_i2c_current())


class DigitalBusCurrentCommand(_NoArgRead):
    help_text = "digital-current [--continuous]         Digital bus current (mA)"

    async def _read(self) -> str:
        return str(await self._hub.get_digital_bus_current())


class ServoCurrentCommand(_NoArgRead):
    help_text = "servo-current [--continuous]           Total servo bus current (mA)"

    async def _read(self) -> str:
        return str(await self._hub.get_servo_current())


class BulkInputCommand(_NoArgRead):
    help_text = (
        "bulkInput [--continuous]               All analog/digital inputs (JSON)"
    )

    async def _read(self) -> str:
        data = await self._hub.get_bulk_input_data()
        return json.dumps(dataclasses.asdict(data), separators=(",", ":"))


# ── Commands with arguments ───────────────────────────────────────────────────


class AnalogCommand(Command):
    help_text = "analog <ch> [--continuous]             ADC input on channel ch (mV)"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)
        if len(rest) != 1:
            return _create_error_action(
                "Expected one argument: channel number (e.g. analog 0)."
            )
        try:
            ch = int(rest[0])
        except ValueError:
            return _create_error_action(f"{rest[0]!r} is not a valid channel number.")

        async def _read() -> str:
            return str(await self._hub.get_analog_input(ch))

        return _create_read_action(_read, continuous)


class BatteryCommand(Command):
    help_text = (
        "battery voltage [--continuous]         Battery voltage (mV)\n"
        "battery current [--continuous]         Battery current (mA)"
    )

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)

        match rest:
            case ["voltage"]:

                async def _read() -> str:
                    return str(await self._hub.get_battery_voltage())

                return _create_read_action(_read, continuous)
            case ["current"]:

                async def _read() -> str:  # type: ignore[misc]
                    return str(await self._hub.get_battery_current())

                return _create_read_action(_read, continuous)
            case _:
                return _create_error_action(
                    f"Unknown subcommand {rest!r}. Expected 'voltage' or 'current'."
                )


class DigitalCommand(Command):
    help_text = (
        "digital read <ch> [--continuous]       Read digital input pin ch\n"
        "digital readall [--continuous]         Read all digital pins as 8-bit field\n"
        "digital write <ch> <high|low|1|0>      Write digital output pin ch\n"
        "digital writeall <bits> <mask>         Write all pins (binary strings)"
    )

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)

        match rest:
            case ["read", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _read() -> str:
                    return str(await self._hub.get_digital_input(ch))

                return _create_read_action(_read, continuous)

            case ["readall"]:

                async def _read() -> str:  # type: ignore[misc]
                    return f"{await self._hub.get_all_digital_inputs():08b}"

                return _create_read_action(_read, continuous)

            case ["write", ch_str, state_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )
                match state_str.lower():
                    case "high" | "1":
                        ds = DigitalState.HIGH
                    case "low" | "0":
                        ds = DigitalState.LOW
                    case _:
                        return _create_error_action(
                            f"Invalid state {state_str!r}: expected high, low, 1, or 0."
                        )

                async def _call() -> str:
                    await digital_write(self._hub, ch, ds)
                    return ""

                return _create_valid_action(_call)

            case ["writeall", bits_str, mask_str]:
                try:
                    bf, bm = int(bits_str, 2), int(mask_str, 2)
                except ValueError:
                    return _create_error_action(
                        f"Bits and mask must be binary strings (e.g. 10110101), "
                        f"got {bits_str!r} and {mask_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await digital_write_all(self._hub, bf, bm)
                    return ""

                return _create_valid_action(_call)

            case _:
                return _create_error_action(
                    f"Unknown subcommand {rest[:1]!r}. Expected read, readall, write, or writeall."
                )


class MotorCommand(Command):
    help_text = (
        "motor power <ch> <power>               Run motor at constant power (−1.0 … 1.0)\n"
        "motor velocity <ch> <speed>            Run at constant velocity (counts/s)\n"
        "motor position <ch> <vel> <pos> <tol>  Move to encoder position\n"
        "motor disable <ch>                     Cut power to motor ch\n"
        "motor encoder <ch> [-r] [--continuous] Read encoder; -r resets count first\n"
        "motor current <ch> [--continuous]      Motor winding current (mA)\n"
        "motor pid set <ch> <p> <i> <d>         Set PID velocity coefficients\n"
        "motor pid get <ch>                     Read PID/PIDF velocity coefficients\n"
        "motor pidf set <ch> <p> <i> <d> <f>   Set PIDF velocity coefficients\n"
        "motor pidf get <ch>                    Read PIDF velocity coefficients\n"
        "motor alert get <ch>                   Read overcurrent alert threshold (mA)\n"
        "motor alert set <ch> <mA>             Set overcurrent alert threshold"
    )

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)
        do_reset, rest = _parse_flag(rest, "-r")

        match rest:
            case ["encoder", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )
                if do_reset:

                    async def _call() -> str:
                        await reset_encoder(self._hub, ch)
                        return f"Encoder {ch} reset."

                    return _create_valid_action(_call)

                async def _read() -> str:
                    return str(await self._hub.get_motor_encoder_position(ch))

                return _create_read_action(_read, continuous)

            case ["current", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _read() -> str:  # type: ignore[misc]
                    return str(await self._hub.get_motor_current(ch))

                return _create_read_action(_read, continuous)

            case ["power", ch_str, power_str]:
                try:
                    ch, power = int(ch_str), float(power_str)
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel and float power, got {ch_str!r} and {power_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await run_motor_constant_power(self._hub, ch, power)
                    return f"Motor {ch} at power {power:.2f}. Use 'motor disable {ch}' to stop."

                return _create_valid_action(_call)

            case ["velocity", ch_str, speed_str]:
                try:
                    ch, speed = int(ch_str), int(speed_str)
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel and speed, got {ch_str!r} and {speed_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await run_motor_constant_velocity(self._hub, ch, speed)
                    return f"Motor {ch} at {speed} counts/s. Use 'motor disable {ch}' to stop."

                return _create_valid_action(_call)

            case ["position", ch_str, vel_str, pos_str, tol_str]:
                try:
                    ch, vel, pos, tol = (
                        int(ch_str),
                        int(vel_str),
                        int(pos_str),
                        int(tol_str),
                    )
                except ValueError:
                    return _create_error_action(
                        f"Expected integers for channel, velocity, position, and tolerance; "
                        f"got {ch_str!r} {vel_str!r} {pos_str!r} {tol_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await run_motor_to_position(self._hub, ch, vel, pos, tol)
                    return ""

                return _create_valid_action(_call)

            case ["disable", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await self._hub.set_motor_channel_enable(ch, False)
                    return f"Motor {ch} disabled."

                return _create_valid_action(_call)

            case ["pid", "set", ch_str, p_str, i_str, d_str]:
                try:
                    ch, p, i, d = int(ch_str), float(p_str), float(i_str), float(d_str)
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel and float p/i/d coefficients; "
                        f"got {ch_str!r} {p_str!r} {i_str!r} {d_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await set_motor_regulated_velocity_pid(self._hub, ch, p, i, d)
                    return ""

                return _create_valid_action(_call)

            case ["pid", "get", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await get_motor_regulated_velocity_pidf(self._hub, ch)
                    return ""

                return _create_valid_action(_call)

            case ["pidf", "set", ch_str, p_str, i_str, d_str, f_str]:
                try:
                    ch = int(ch_str)
                    p, i, d, f = float(p_str), float(i_str), float(d_str), float(f_str)
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel and float p/i/d/f coefficients; "
                        f"got {ch_str!r} {p_str!r} {i_str!r} {d_str!r} {f_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await set_motor_regulated_velocity_pidf(self._hub, ch, p, i, d, f)
                    return ""

                return _create_valid_action(_call)

            case ["pidf", "get", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await get_motor_regulated_velocity_pidf(self._hub, ch)
                    return ""

                return _create_valid_action(_call)

            case ["alert", "get", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    ma = await get_motor_alert_level_ma(self._hub, ch)
                    return f"Motor alert for channel {ch} is {ma} mA"

                return _create_valid_action(_call)

            case ["alert", "set", ch_str, ma_str]:
                try:
                    ch, ma = int(ch_str), int(ma_str)
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel and mA threshold, got {ch_str!r} and {ma_str!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await set_motor_alert_level(self._hub, ch, ma)
                    return ""

                return _create_valid_action(_call)

            case _:
                return _create_error_action(
                    f"Unknown motor subcommand {rest[:1]!r}. "
                    "Expected power, velocity, position, disable, encoder, current, "
                    "pid, pidf, or alert."
                )


class ServoCommand(Command):
    help_text = (
        "servo <ch> <pulse_width> [frame_width]  Enable servo; frame default 4000 µs\n"
        "servo disable <ch>                      Disable servo ch"
    )

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        match rest:
            case ["disable", ch_str]:
                try:
                    ch = int(ch_str)
                except ValueError:
                    return _create_error_action(
                        f"{ch_str!r} is not a valid channel number."
                    )

                async def _call() -> str:
                    await self._hub.set_servo_enable(ch, False)
                    return f"Servo {ch} disabled."

                return _create_valid_action(_call)

            case [ch_str, pw_str] | [ch_str, pw_str, _]:
                try:
                    ch, pw = int(ch_str), int(pw_str)
                    fw = int(rest[2]) if len(rest) == 3 else 4000
                except ValueError:
                    return _create_error_action(
                        f"Expected integer channel, pulse width, and optional frame width; "
                        f"got {' '.join(rest)!r}."
                    )

                async def _call() -> str:  # type: ignore[misc]
                    await run_servo(self._hub, ch, pw, fw)
                    return f"Servo {ch} running. Use 'servo disable {ch}' to stop."

                return _create_valid_action(_call)

            case _:
                return _create_error_action(
                    "Expected: servo <ch> <pulse_width> [frame_width]  or  servo disable <ch>."
                )


class DistanceCommand(Command):
    help_text = "distance <ch> [--continuous]          Distance sensor reading (mm)"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        continuous, rest = _parse_continuous_flag(rest)
        if len(rest) != 1:
            return _create_error_action(
                "Expected one argument: channel number (e.g. distance 0)."
            )
        try:
            ch = int(rest[0])
        except ValueError:
            return _create_error_action(f"{rest[0]!r} is not a valid channel number.")

        from rev_distance_sensor import DistanceSensor  # optional dep

        sensor = DistanceSensor(self._hub, ch)
        setup_done = False

        async def _read() -> str:
            nonlocal setup_done
            if not setup_done:
                await sensor.setup()
                setup_done = True
            return str(await sensor.get_distance_millimeters())

        return _create_read_action(_read, continuous)


class LedSetCommand(Command):
    help_text = "led <r> <g> <b>                        Set hub LED color (0–255 each)"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if len(rest) != 3:
            return _create_error_action("Expected three arguments: r g b (0–255 each).")
        try:
            r, g, b = int(rest[0]), int(rest[1]), int(rest[2])
        except ValueError:
            return _create_error_action(
                f"R, G, B values must be integers 0–255; got {rest[0]!r} {rest[1]!r} {rest[2]!r}."
            )

        async def _call() -> str:
            await led(self._hub, r, g, b)
            return ""

        return _create_valid_action(_call)


class GetLedCommand(Command):
    help_text = "get-led                                Read current LED color"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )

        async def _call() -> str:
            await get_led(self._hub)
            return ""

        return _create_valid_action(_call)


class PatternCommand(Command):
    help_text = "pattern <step> [<step> ...]            Set LED animation pattern"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if not rest:
            return _create_error_action("Expected at least one pattern step.")

        steps = list(rest)

        async def _call() -> str:
            await led_pattern(self._hub, steps)
            await get_led_pattern(self._hub)
            return ""

        return _create_valid_action(_call)


class GetPatternCommand(Command):
    help_text = "get-pattern                            Read current LED pattern"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )

        async def _call() -> str:
            await get_led_pattern(self._hub)
            return ""

        return _create_valid_action(_call)


class VersionCommand(Command):
    help_text = "version                                Firmware and hardware version"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )

        async def _call() -> str:
            await firmware_version(self._hub)
            return ""

        return _create_valid_action(_call)


class QueryCommand(Command):
    help_text = "query <name>                           Query an interface by name"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if len(rest) != 1:
            return _create_error_action(
                "Expected one argument: interface name (e.g. query DeviceInterfaceModule)."
            )
        name = rest[0]

        async def _call() -> str:
            await query_interface(self._hub, name)
            return ""

        return _create_valid_action(_call)


class LogCommand(Command):
    help_text = "log <text>                             Inject a hint into the hub data log (≤100 chars)"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if not rest:
            return _create_error_action("Expected log text (e.g. log my note here).")

        text = " ".join(rest)

        async def _call() -> str:
            await inject_log(self._hub, text)
            return ""

        return _create_valid_action(_call)


class LoglevelCommand(Command):
    help_text = (
        "loglevel <group> <level>               Set debug log verbosity (level 0–3)"
    )

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if len(rest) != 2:
            return _create_error_action(
                "Expected two arguments: group name and level (0–3)."
            )
        try:
            level = int(rest[1])
        except ValueError:
            return _create_error_action(f"{rest[1]!r} is not a valid integer level.")
        if level not in (0, 1, 2, 3):
            return _create_error_action(f"Level must be 0, 1, 2, or 3 (got {level}).")
        group = rest[0]

        async def _call() -> str:
            await set_debug_log_level(self._hub, group, level)
            return ""

        return _create_valid_action(_call)


class FailsafeCommand(Command):
    help_text = "failsafe                               Trigger fail-safe demonstration"

    def __init__(self, hub: ExpansionHub) -> None:
        self._hub = hub

    def parse(self, rest: list[str]) -> CommandAction:
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )

        async def _call() -> str:
            await send_fail_safe(self._hub, lambda: None)
            return ""

        return _create_valid_action(_call)


# ── Watch command ─────────────────────────────────────────────────────────────


class WatchCommand(Command):
    help_text = (
        "watch add [--rate <hz>] <command...>   Add a live-updating watch widget\n"
        "watch list                             List active watches\n"
        "watch close <n>                        Close watch n"
    )

    def __init__(
        self,
        registry: dict[str, Command],
        add_fn: Any,
        close_fn: Any,
        watches: dict[int, Any],
    ) -> None:
        self._registry = registry
        self._add_fn = add_fn
        self._close_fn = close_fn
        self._watches = watches

    def parse(self, rest: list[str]) -> CommandAction:
        if not rest:
            return _create_error_action("Expected a subcommand: add, list, or close.")
        match rest[0]:
            case "add":
                return self._parse_add(rest[1:])
            case "list":
                return self._parse_list()
            case "close":
                return self._parse_close(rest[1:])
            case _:
                return _create_error_action(
                    f"Unknown watch subcommand {rest[0]!r}. Expected add, list, or close."
                )

    def _parse_add(self, rest: list[str]) -> CommandAction:
        rate = 1.0
        if rest[:1] == ["--rate"]:
            if len(rest) < 2:
                return _create_error_action(
                    "--rate requires a value (e.g. --rate 2.0)."
                )
            try:
                rate = float(rest[1])
            except ValueError:
                return _create_error_action(
                    f"{rest[1]!r} is not a valid rate (expected a number)."
                )
            rest = rest[2:]

        if not rest:
            return _create_error_action(
                "Expected a watchable command after the rate (e.g. watch add analog 0)."
            )

        command = self._registry.get(rest[0])
        label = " ".join(rest)

        if command is None:
            return _create_error_action(
                f"Unknown command {rest[0]!r}. Type help for watchable commands."
            )

        sub = command.parse(rest[1:])
        if not sub.valid:
            return _create_error_action(sub.error or f"Cannot watch {label!r}.")
        if not sub.watchable:
            return _create_error_action(
                f"{label!r} is not watchable. Type help for watchable commands."
            )

        reader = sub.call
        add_fn = self._add_fn

        async def _call() -> str:  # type: ignore[misc]
            wid = await add_fn(label, reader, rate)
            return f"Watch [{wid}] started: {label} at {rate} Hz"

        return _create_valid_action(_call)

    def _parse_list(self) -> CommandAction:
        watches = self._watches

        async def _call() -> str:
            if not watches:
                return "No active watches."
            return "\n".join(
                f"[{wid}] {w._label}  ({w._rate} Hz / {1.0 / w._rate:.2f}s)"
                for wid, w in sorted(watches.items())
            )

        return _create_valid_action(_call)

    def _parse_close(self, rest: list[str]) -> CommandAction:
        if len(rest) != 1:
            return _create_error_action(
                "Expected one argument: watch number (e.g. watch close 1)."
            )
        try:
            n = int(rest[0])
        except ValueError:
            return _create_error_action(f"{rest[0]!r} is not a valid watch number.")
        close_fn = self._close_fn

        async def _call() -> str:
            return close_fn(n)

        return _create_valid_action(_call)


# ── Help command ──────────────────────────────────────────────────────────────

_HELP_SECTIONS = [
    (
        "Analog / power readings",
        [
            "temperature",
            "5vRailVoltage",
            "i2c-current",
            "digital-current",
            "servo-current",
            "bulkInput",
            "analog",
            "battery",
        ],
    ),
    ("Digital I/O", ["digital"]),
    ("Motor control", ["motor"]),
    ("Servo control", ["servo"]),
    ("Distance sensor", ["distance"]),
    ("LED", ["led", "get-led", "pattern", "get-pattern"]),
    ("Misc", ["version", "query", "log", "loglevel", "failsafe"]),
    ("Watch panel", ["watch"]),
    ("Session", ["help"]),
]


def _build_help(registry: dict[str, Command]) -> str:
    lines: list[str] = []
    for section, names in _HELP_SECTIONS:
        lines.append(section)
        for name in names:
            cmd = registry.get(name)
            if cmd:
                for line in cmd.help_text.splitlines():
                    lines.append("  " + line)
    lines.append("")
    lines.append("Keys: Ctrl+C — cancel --continuous · Ctrl+Q — quit")
    return "\n".join(lines)


class HelpCommand(Command):
    help_text = "help                                   Show this reference"

    def __init__(self, registry: dict[str, Command]) -> None:
        self._registry = registry

    def parse(self, rest: list[str]) -> CommandAction:
        if rest:
            return _create_error_action(
                f"This command takes no arguments (got {rest!r})."
            )
        registry = self._registry

        async def _call() -> str:
            return _build_help(registry)

        return _create_valid_action(_call)
