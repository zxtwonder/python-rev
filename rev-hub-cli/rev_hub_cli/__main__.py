#!/usr/bin/env python3
"""rev-hub — Command-line tool for REV Robotics Expansion Hubs."""

from __future__ import annotations

import asyncio
import sys

import click

from rev_core.digital_state import DigitalState
from rev_core.expansion_hub import ExpansionHub
from rev_core.rev_hub import ParentRevHub, RevHub
from rev_expansion_hub import (
    get_possible_expansion_hub_serial_numbers,
    open_connected_expansion_hubs,
    open_parent_expansion_hub,
)
from rev_hub_cli.hub_stringify import hub_hierarchy_to_string
from rev_hub_cli.command.analog import (
    analog,
    battery_current,
    battery_voltage,
    digital_bus_current,
    i2c_current,
    motor_current,
    servo_current,
    temperature,
    voltage_rail,
)
from rev_hub_cli.command.bulk_input import get_bulk_input_data
from rev_hub_cli.command.digital import (
    digital_read,
    digital_read_all,
    digital_write,
    digital_write_all,
)
from rev_hub_cli.command.distance import distance
from rev_hub_cli.command.error import error
from rev_hub_cli.command.failsafe import send_fail_safe
from rev_hub_cli.command.firmware_version import firmware_version
from rev_hub_cli.command.led import get_led, get_led_pattern, led, led_pattern
from rev_hub_cli.command.log import inject_log, set_debug_log_level
from rev_hub_cli.command.motor import (
    get_motor_alert_level_ma,
    get_motor_regulated_velocity_pidf,
    read_encoder,
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


def _run(coro):
    """Run an async coroutine from a synchronous Click action."""
    try:
        return asyncio.run(coro)
    except Exception as e:
        click.echo(f"Encountered unexpected error:\n{e}", err=True)
        sys.exit(1)


# ── Global options ────────────────────────────────────────────────────────────

@click.group()
@click.version_option("1.0.0")
@click.option("-s", "--serial", "serial_number", help="Serial number of the parent hub (starts with DQ)")
@click.option("-p", "--parent", "parent_address", type=int, help="Module address of the parent hub")
@click.option("-c", "--child", "child_address", type=int, help="Module address of a child hub (requires --parent)")
@click.pass_context
def cli(ctx: click.Context, serial_number: str | None, parent_address: int | None, child_address: int | None) -> None:
    """rev-hub — CLI for REV Robotics Expansion Hubs."""
    ctx.ensure_object(dict)
    ctx.obj["serial"] = serial_number
    ctx.obj["parent"] = parent_address
    ctx.obj["child"] = child_address


# ── Hub selection helper ──────────────────────────────────────────────────────

async def _get_expansion_hub(
    serial_number: str | None,
    parent_address: int | None,
    child_address: int | None,
) -> tuple[ExpansionHub, callable]:
    """Return ``(hub, close)`` based on the provided addressing options."""
    if child_address is not None and not (1 <= child_address <= 255):
        raise click.ClickException(f"{child_address} is not a valid child address")
    if parent_address is not None and not (1 <= parent_address <= 255):
        raise click.ClickException(f"{parent_address} is not a valid parent address")
    if child_address is not None and parent_address is None:
        raise click.ClickException("A child address cannot be specified without a parent address.")

    if serial_number is not None:
        if parent_address is None:
            raise click.ClickException("--parent must be specified when --serial is given.")
        return await _open_with_serial(serial_number, parent_address, child_address)
    if parent_address is not None:
        return await _open_with_address(parent_address, child_address)

    hubs = await open_connected_expansion_hubs()
    if not hubs:
        raise click.ClickException("No hubs are connected")
    if len(hubs) > 1:
        raise click.ClickException("Multiple hubs connected. You must specify --serial.")

    def close_all():
        for h in hubs:
            h.close()

    return hubs[0], close_all


async def _open_with_serial(
    serial_number: str,
    parent_address: int,
    child_address: int | None,
) -> tuple[ExpansionHub, callable]:
    parent = await open_parent_expansion_hub(serial_number, parent_address)
    if child_address is None or child_address == parent.module_address:
        return parent, parent.close
    child = await parent.add_child_by_address(child_address)
    if child.is_expansion_hub():
        return child, lambda: (parent.close(), child.close())
    raise click.ClickException(f"Hub ({serial_number}) {child_address} is not an Expansion Hub")


async def _open_with_address(
    parent_address: int,
    child_address: int | None,
) -> tuple[ExpansionHub, callable]:
    serial_numbers = await get_possible_expansion_hub_serial_numbers()
    if len(serial_numbers) > 1:
        raise click.ClickException(
            f"There are {len(serial_numbers)} parent hubs. Please specify --serial."
        )
    parent = await open_parent_expansion_hub(serial_numbers[0], parent_address)
    if child_address is None or child_address == parent_address:
        return parent, parent.close
    child = await parent.add_child_by_address(child_address)
    if child.is_expansion_hub():
        return child, parent.close
    raise click.ClickException(f"No expansion hub found with module address {child_address}")


# ── Commands ──────────────────────────────────────────────────────────────────

@cli.command("testErrorHandling")
def cmd_error() -> None:
    """Intentionally cause errors and print information about them."""
    _run(error())


@cli.command("list")
def cmd_list() -> None:
    """List all connected expansion hubs."""
    async def _list():
        hubs = await open_connected_expansion_hubs()
        for hub in hubs:
            hub.on("error", lambda e: click.echo(f"Got error:\n{e}"))
            click.echo(hub_hierarchy_to_string(hub))
        await asyncio.sleep(2)
        for hub in hubs:
            hub.close()
    _run(_list())


@cli.command("pattern")
@click.argument("steps", nargs=-1, required=True)
@click.pass_context
def cmd_pattern(ctx: click.Context, steps: tuple[str, ...]) -> None:
    """Run LED pattern. Steps: <time><RRGGBB>, e.g. '100FF00' for 1s green."""
    async def _pattern():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await led_pattern(hub, list(steps))
        await get_led_pattern(hub)
        close()
    _run(_pattern())


@cli.command("get-pattern")
@click.pass_context
def cmd_get_pattern(ctx: click.Context) -> None:
    """Get the current LED pattern steps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await get_led_pattern(hub)
        close()
    _run(_go())


@cli.command("led")
@click.argument("r", type=int)
@click.argument("g", type=int)
@click.argument("b", type=int)
@click.pass_context
def cmd_led(ctx: click.Context, r: int, g: int, b: int) -> None:
    """Set LED color (values 0–255)."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await led(hub, r, g, b)
        close()
    _run(_go())


@cli.command("get-led")
@click.pass_context
def cmd_get_led(ctx: click.Context) -> None:
    """Get the current LED color."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await get_led(hub)
        close()
    _run(_go())


@cli.command("query")
@click.argument("name")
@click.pass_context
def cmd_query(ctx: click.Context, name: str) -> None:
    """Query interface information by name."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await query_interface(hub, name)
        close()
    _run(_go())


@cli.command("bulkInput")
@click.option("--continuous", is_flag=True, help="Run continuously")
@click.pass_context
def cmd_bulk_input(ctx: click.Context, continuous: bool) -> None:
    """Get all input data at once."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await get_bulk_input_data(hub, continuous)
        close()
    _run(_go())


@cli.command("failsafe")
@click.pass_context
def cmd_failsafe(ctx: click.Context) -> None:
    """Start servo 0, send fail-safe after 2s, then close after 2 more seconds."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await send_fail_safe(hub, close)
    _run(_go())


@cli.command("version")
@click.pass_context
def cmd_version(ctx: click.Context) -> None:
    """Get firmware version."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await firmware_version(hub)
        close()
    _run(_go())


# ── digital subcommand group ──────────────────────────────────────────────────

@cli.group("digital")
def digital_group() -> None:
    """Digital I/O commands."""


@digital_group.command("write")
@click.argument("channel", type=int)
@click.argument("state")
@click.pass_context
def cmd_digital_write(ctx: click.Context, channel: int, state: str) -> None:
    """Write a digital pin. STATE is one of: high, low, 1, 0."""
    if state in ("high", "1"):
        ds = DigitalState.HIGH
    elif state in ("low", "0"):
        ds = DigitalState.LOW
    else:
        raise click.ClickException("Please provide only one of {high, low, 1, 0}")

    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await digital_write(hub, channel, ds)
        close()
    _run(_go())


@digital_group.command("read")
@click.argument("channel", type=int)
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_digital_read(ctx: click.Context, channel: int, continuous: bool) -> None:
    """Read a digital input pin."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await digital_read(hub, channel, continuous)
        close()
    _run(_go())


@digital_group.command("readall")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_digital_read_all(ctx: click.Context, continuous: bool) -> None:
    """Read all digital input pins."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await digital_read_all(hub, continuous)
        close()
    _run(_go())


@digital_group.command("writeall")
@click.argument("bitfield")
@click.argument("bitmask")
@click.pass_context
def cmd_digital_write_all(ctx: click.Context, bitfield: str, bitmask: str) -> None:
    """Write all digital pins. BITFIELD and BITMASK are binary strings (e.g. 10110101)."""
    bf = int(bitfield, 2)
    bm = int(bitmask, 2)

    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await digital_write_all(hub, bf, bm)
        close()
    _run(_go())


# ── motor subcommand group ────────────────────────────────────────────────────

@cli.group("motor")
def motor_group() -> None:
    """Motor control commands."""


@motor_group.command("current")
@click.argument("channel", type=int)
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_motor_current(ctx: click.Context, channel: int, continuous: bool) -> None:
    """Read motor current in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await motor_current(hub, channel, continuous)
        close()
    _run(_go())


@motor_group.command("encoder")
@click.argument("channel", type=int)
@click.option("-r", "--reset", "do_reset", is_flag=True, help="Reset the encoder count")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_encoder(ctx: click.Context, channel: int, do_reset: bool, continuous: bool) -> None:
    """Get (or reset) the encoder position for a motor."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        if do_reset:
            await reset_encoder(hub, channel)
        else:
            await read_encoder(hub, channel, continuous)
        close()
    _run(_go())


@motor_group.command("power")
@click.argument("channel", type=int)
@click.argument("power", type=float)
@click.pass_context
def cmd_motor_power(ctx: click.Context, channel: int, power: float) -> None:
    """Run a motor at constant power [-1.0, 1.0]."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await run_motor_constant_power(hub, channel, power)
    _run(_go())


@motor_group.command("velocity")
@click.argument("channel", type=int)
@click.argument("speed", type=int)
@click.pass_context
def cmd_motor_velocity(ctx: click.Context, channel: int, speed: int) -> None:
    """Run a motor at a constant velocity (counts per second)."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await run_motor_constant_velocity(hub, channel, speed)
    _run(_go())


@motor_group.command("position")
@click.argument("channel", type=int)
@click.argument("velocity", type=int)
@click.argument("position", type=int)
@click.argument("tolerance", type=int)
@click.pass_context
def cmd_motor_position(
    ctx: click.Context, channel: int, velocity: int, position: int, tolerance: int
) -> None:
    """Run a motor to a target position."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await run_motor_to_position(hub, channel, velocity, position, tolerance)
    _run(_go())


@motor_group.group("pid")
def pid_group() -> None:
    """Get or set PID coefficients."""


@pid_group.command("set")
@click.argument("channel", type=int)
@click.argument("p", type=float)
@click.argument("i", type=float)
@click.argument("d", type=float)
@click.pass_context
def cmd_pid_set(ctx: click.Context, channel: int, p: float, i: float, d: float) -> None:
    """Set PID coefficients for regulated velocity mode."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await set_motor_regulated_velocity_pid(hub, channel, p, i, d)
        close()
    _run(_go())


@pid_group.command("get")
@click.argument("channel", type=int)
@click.pass_context
def cmd_pid_get(ctx: click.Context, channel: int) -> None:
    """Get PID/PIDF coefficients for regulated velocity mode."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await get_motor_regulated_velocity_pidf(hub, channel)
        close()
    _run(_go())


@motor_group.group("pidf")
def pidf_group() -> None:
    """Get or set PIDF coefficients."""


@pidf_group.command("set")
@click.argument("channel", type=int)
@click.argument("p", type=float)
@click.argument("i", type=float)
@click.argument("d", type=float)
@click.argument("f", type=float)
@click.pass_context
def cmd_pidf_set(
    ctx: click.Context, channel: int, p: float, i: float, d: float, f: float
) -> None:
    """Set PIDF coefficients for regulated velocity mode."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await set_motor_regulated_velocity_pidf(hub, channel, p, i, d, f)
        close()
    _run(_go())


@pidf_group.command("get")
@click.argument("channel", type=int)
@click.pass_context
def cmd_pidf_get(ctx: click.Context, channel: int) -> None:
    """Get PIDF coefficients for regulated velocity mode."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await get_motor_regulated_velocity_pidf(hub, channel)
        close()
    _run(_go())


@motor_group.group("alert")
def alert_group() -> None:
    """Get or set motor alert current (mA)."""


@alert_group.command("get")
@click.argument("channel", type=int)
@click.pass_context
def cmd_alert_get(ctx: click.Context, channel: int) -> None:
    """Get the motor alert current threshold in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        current = await get_motor_alert_level_ma(hub, channel)
        click.echo(f"Motor alert for channel {channel} is {current} mA")
        close()
    _run(_go())


@alert_group.command("set")
@click.argument("channel", type=int)
@click.argument("current", type=int)
@click.pass_context
def cmd_alert_set(ctx: click.Context, channel: int, current: int) -> None:
    """Set the motor alert current threshold in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await set_motor_alert_level(hub, channel, current)
        close()
    _run(_go())


# ── Remaining top-level commands ──────────────────────────────────────────────

@cli.command("distance")
@click.argument("channel", type=int)
@click.option("--continuous", is_flag=True)
def cmd_distance(channel: int, continuous: bool) -> None:
    """Read distance from a REV 2m distance sensor."""
    async def _go():
        hubs = await open_connected_expansion_hubs()
        hub = hubs[0]
        await distance(hub, channel, continuous)
        hub.close()
    _run(_go())


@cli.command("analog")
@click.argument("port", type=int)
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_analog(ctx: click.Context, port: int, continuous: bool) -> None:
    """Read the analog value of a port in millivolts."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await analog(hub, port, continuous)
        close()
    _run(_go())


@cli.command("temperature")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_temperature(ctx: click.Context, continuous: bool) -> None:
    """Read the hub temperature in Celsius."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await temperature(hub, continuous)
        close()
    _run(_go())


@cli.command("5vRailVoltage")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_5v_rail(ctx: click.Context, continuous: bool) -> None:
    """Read the 5V rail voltage in millivolts."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await voltage_rail(hub, continuous)
        close()
    _run(_go())


@cli.group("battery")
def battery_group() -> None:
    """Battery information commands."""


@battery_group.command("voltage")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_battery_voltage(ctx: click.Context, continuous: bool) -> None:
    """Read the battery voltage in millivolts."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await battery_voltage(hub, continuous)
        close()
    _run(_go())


@battery_group.command("current")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_battery_current(ctx: click.Context, continuous: bool) -> None:
    """Read the battery current in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await battery_current(hub, continuous)
        close()
    _run(_go())


@cli.command("i2c-current")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_i2c_current(ctx: click.Context, continuous: bool) -> None:
    """Read the I2C sub-system current in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await i2c_current(hub, continuous)
        close()
    _run(_go())


@cli.command("digital-current")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_digital_current(ctx: click.Context, continuous: bool) -> None:
    """Read the digital bus current in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await digital_bus_current(hub, continuous)
        close()
    _run(_go())


@cli.command("servo-current")
@click.option("--continuous", is_flag=True)
@click.pass_context
def cmd_servo_current(ctx: click.Context, continuous: bool) -> None:
    """Read the total servo current in milliamps."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await servo_current(hub, continuous)
        close()
    _run(_go())


@cli.command("log")
@click.argument("text")
@click.pass_context
def cmd_log(ctx: click.Context, text: str) -> None:
    """Inject a log hint into the UART data stream."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await inject_log(hub, text)
        close()
    _run(_go())


@cli.command("loglevel")
@click.argument("group")
@click.argument("level", type=int)
@click.pass_context
def cmd_loglevel(ctx: click.Context, group: str, level: int) -> None:
    """Set the debug log level for a group (0–3).

    GROUP is one of: Main, TransmitterToHost, ReceiverFromHost, ADC,
    PWMAndServo, ModuleLED, DigitalIO, I2C, Motor0, Motor1, Motor2, Motor3.
    """
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await set_debug_log_level(hub, group, level)
        close()
    _run(_go())


@cli.command("servo")
@click.argument("channel", type=int)
@click.argument("pulse_width", type=int)
@click.argument("frame_width", type=int, default=4000)
@click.pass_context
def cmd_servo(ctx: click.Context, channel: int, pulse_width: int, frame_width: int) -> None:
    """Run a servo with a given pulse width and optional frame width."""
    async def _go():
        hub, close = await _get_expansion_hub(**ctx.obj)
        await run_servo(hub, channel, pulse_width, frame_width)
    _run(_go())


if __name__ == "__main__":
    cli()
