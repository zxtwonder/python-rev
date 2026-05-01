"""rev_rhsplib — async Python wrappers around the _rev_rhsplib C extension.

All methods on :class:`Serial` and :class:`RevHub` are coroutines.  Blocking
librhsp calls are executed in the default thread-pool executor so they never
stall the asyncio event loop.  A per-hub :class:`asyncio.Lock` serialises
concurrent calls on the same hub instance.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from rev_rhsplib._rev_rhsplib import (
    Serial as _Serial,
    RevHub as _RevHub,
    SerialParity,
    SerialFlowControl,
    RhspLibError,
    RhspLibErrorCode,
    SerialErrorCode,
)

__all__ = [
    "Serial",
    "RevHub",
    "SerialParity",
    "SerialFlowControl",
    "RhspLibError",
    "RhspLibErrorCode",
    "SerialErrorCode",
]


def _run(fn: Callable[..., Any], *args: Any) -> Any:
    """Run a blocking function in the default executor (returns a coroutine)."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, fn, *args)


class Serial:
    """Async wrapper around the C-level ``Serial`` class.

    Represents an open serial port used to communicate with a REV Hub.
    """

    def __init__(self) -> None:
        self._native = _Serial()

    async def open(
        self,
        port: str,
        baudrate: int,
        databits: int,
        parity: SerialParity,
        stopbits: int,
        flow_control: SerialFlowControl,
    ) -> None:
        """Open the serial port.

        :param port: Port path (e.g. ``"/dev/ttyUSB0"`` or ``"COM3"``).
        :param baudrate: Baud rate (REV Hubs use 460800).
        :param databits: Data bits (REV Hubs use 8).
        :param parity: Parity setting.
        :param stopbits: Stop bits (REV Hubs use 1).
        :param flow_control: Flow control setting.
        """
        await _run(self._native.open, port, baudrate, databits, parity, stopbits, flow_control)

    def close(self) -> None:
        """Close the serial port synchronously."""
        self._native.close()

    async def read(self, num_bytes: int) -> list[int]:
        """Read up to *num_bytes* bytes from the serial port."""
        return await _run(self._native.read, num_bytes)

    async def write(self, bytes_: list[int]) -> None:
        """Write *bytes_* to the serial port."""
        await _run(self._native.write, bytes_)

    def get_native(self) -> _Serial:
        """Return the underlying C-level Serial object."""
        return self._native


class RevHub:
    """Async wrapper around the C-level ``RevHub`` class.

    Represents a single REV Expansion Hub module.  Wrap all hub operations in
    a per-instance lock so that concurrent coroutines do not interleave serial
    frames.
    """

    def __init__(self) -> None:
        self._native = _RevHub()
        self._lock = asyncio.Lock()

    async def open(self, serial: Serial, dest_address: int) -> None:
        """Allocate and open the hub at the given module address.

        :param serial: An open :class:`Serial` port shared by this bus.
        :param dest_address: RS-485 destination address.
        """
        async with self._lock:
            await _run(self._native.open, serial.get_native(), dest_address)

    def is_opened(self) -> bool:
        """Return True if the hub is currently open."""
        return self._native.is_opened()

    def close(self) -> None:
        """Close the hub synchronously and free all C resources."""
        self._native.close()

    def set_dest_address(self, addr: int) -> None:
        """Set the destination address (synchronous — no serial I/O)."""
        self._native.set_dest_address(addr)

    def get_dest_address(self) -> int:
        """Return the current destination address."""
        return self._native.get_dest_address()

    def set_response_timeout_ms(self, ms: int) -> None:
        """Set the response timeout in milliseconds (0 = infinite)."""
        self._native.set_response_timeout_ms(ms)

    def get_response_timeout_ms(self) -> int:
        """Return the response timeout in milliseconds."""
        return self._native.get_response_timeout_ms()

    # ── Custom commands ───────────────────────────────────────────────────

    async def send_write_command(self, packet_type_id: int, payload: list[int]) -> list[int]:
        """Send a raw write command and return the response payload bytes."""
        async with self._lock:
            return await _run(self._native.send_write_command, packet_type_id, payload)

    async def send_read_command(self, packet_type_id: int, payload: list[int]) -> list[int]:
        """Send a raw read command and return the response payload bytes."""
        async with self._lock:
            return await _run(self._native.send_read_command, packet_type_id, payload)

    # ── Module status / control ───────────────────────────────────────────

    async def get_module_status(self, clear: bool) -> dict:
        """Return a dict with ``status_word`` and ``motor_alerts``."""
        async with self._lock:
            return await _run(self._native.get_module_status, clear)

    async def send_keep_alive(self) -> None:
        """Send a keep-alive packet."""
        async with self._lock:
            await _run(self._native.send_keep_alive)

    async def send_fail_safe(self) -> None:
        """Trigger the hub fail-safe."""
        async with self._lock:
            await _run(self._native.send_fail_safe)

    async def set_new_module_address(self, new_addr: int) -> None:
        """Permanently change the hub's module address."""
        async with self._lock:
            await _run(self._native.set_new_module_address, new_addr)

    async def query_interface(self, name: str) -> dict:
        """Return a dict with ``name``, ``first_packet_id``, ``number_id_values``."""
        async with self._lock:
            return await _run(self._native.query_interface, name)

    async def get_interface_packet_id(self, name: str, function_number: int) -> int:
        """Return the packet type ID for the given interface function."""
        async with self._lock:
            return await _run(self._native.get_interface_packet_id, name, function_number)

    async def set_debug_log_level(self, group: int, level: int) -> None:
        """Set the log verbosity for a debug group."""
        async with self._lock:
            await _run(self._native.set_debug_log_level, group, level)

    # ── LED ──────────────────────────────────────────────────────────────

    async def set_module_led_color(self, red: int, green: int, blue: int) -> None:
        """Set the onboard RGB LED color."""
        async with self._lock:
            await _run(self._native.set_module_led_color, red, green, blue)

    async def get_module_led_color(self) -> tuple[int, int, int]:
        """Return ``(red, green, blue)`` tuple."""
        async with self._lock:
            return await _run(self._native.get_module_led_color)

    async def set_module_led_pattern(self, steps: list[int]) -> None:
        """Set the LED animation pattern (list of 16 packed RGBT uint32 values)."""
        async with self._lock:
            await _run(self._native.set_module_led_pattern, steps)

    async def get_module_led_pattern(self) -> list[int]:
        """Return the current LED pattern as a list of 16 packed RGBT uint32 values."""
        async with self._lock:
            return await _run(self._native.get_module_led_pattern)

    # ── Device control ────────────────────────────────────────────────────

    async def get_bulk_input_data(self) -> dict:
        """Return a dict matching the fields of :class:`~rev_core.BulkInputData`."""
        async with self._lock:
            return await _run(self._native.get_bulk_input_data)

    async def get_adc(self, channel: int, raw_mode: int) -> int:
        """Read an ADC channel value."""
        async with self._lock:
            return await _run(self._native.get_adc, channel, raw_mode)

    async def phone_charge_control(self, enable: bool) -> None:
        """Enable or disable phone charging."""
        async with self._lock:
            await _run(self._native.phone_charge_control, enable)

    async def phone_charge_query(self) -> bool:
        """Return True if phone charging is enabled."""
        async with self._lock:
            return await _run(self._native.phone_charge_query)

    async def inject_data_log_hint(self, hint: str) -> None:
        """Inject a log hint string."""
        async with self._lock:
            await _run(self._native.inject_data_log_hint, hint)

    async def read_version_string(self) -> str:
        """Return the firmware/hardware version as a human-readable string."""
        async with self._lock:
            return await _run(self._native.read_version_string)

    async def read_version(self) -> dict:
        """Return a dict matching the fields of :class:`~rev_core.Version`."""
        async with self._lock:
            return await _run(self._native.read_version)

    async def ftdi_reset_control(self, enable: bool) -> None:
        """Control FTDI reset on keep-alive timeout."""
        async with self._lock:
            await _run(self._native.ftdi_reset_control, enable)

    async def ftdi_reset_query(self) -> bool:
        """Return True if FTDI reset on timeout is enabled."""
        async with self._lock:
            return await _run(self._native.ftdi_reset_query)

    # ── Digital I/O ──────────────────────────────────────────────────────

    async def set_single_digital_output(self, pin: int, value: bool) -> None:
        """Set a single digital output pin."""
        async with self._lock:
            await _run(self._native.set_single_digital_output, pin, value)

    async def set_all_digital_outputs(self, packed: int) -> None:
        """Set all digital output pins from a bit-packed field."""
        async with self._lock:
            await _run(self._native.set_all_digital_outputs, packed)

    async def set_digital_direction(self, pin: int, direction_output: int) -> None:
        """Set a digital pin direction (0=input, 1=output)."""
        async with self._lock:
            await _run(self._native.set_digital_direction, pin, direction_output)

    async def get_digital_direction(self, pin: int) -> int:
        """Return the direction of a digital pin (0=input, 1=output)."""
        async with self._lock:
            return await _run(self._native.get_digital_direction, pin)

    async def get_single_digital_input(self, pin: int) -> bool:
        """Read a single digital input pin."""
        async with self._lock:
            return await _run(self._native.get_single_digital_input, pin)

    async def get_all_digital_inputs(self) -> int:
        """Read all digital inputs as a bit-packed integer."""
        async with self._lock:
            return await _run(self._native.get_all_digital_inputs)

    # ── I2C ──────────────────────────────────────────────────────────────

    async def configure_i2c_channel(self, channel: int, speed_code: int) -> None:
        """Configure the speed of an I2C channel."""
        async with self._lock:
            await _run(self._native.configure_i2c_channel, channel, speed_code)

    async def configure_i2c_query(self, channel: int) -> int:
        """Return the speed code of an I2C channel."""
        async with self._lock:
            return await _run(self._native.configure_i2c_query, channel)

    async def write_single_byte(self, channel: int, addr: int, byte: int) -> None:
        """Write a single byte to an I2C device."""
        async with self._lock:
            await _run(self._native.write_single_byte, channel, addr, byte)

    async def write_multiple_bytes(self, channel: int, addr: int, bytes_: list[int]) -> None:
        """Write multiple bytes to an I2C device."""
        async with self._lock:
            await _run(self._native.write_multiple_bytes, channel, addr, bytes_)

    async def write_status_query(self, channel: int) -> dict:
        """Return I2C write status dict with ``i2c_transaction_status`` and ``num_bytes_written``."""
        async with self._lock:
            return await _run(self._native.write_status_query, channel)

    async def read_single_byte(self, channel: int, addr: int) -> None:
        """Initiate an I2C single-byte read (fire and forget — poll with read_status_query)."""
        async with self._lock:
            await _run(self._native.read_single_byte, channel, addr)

    async def read_multiple_bytes(self, channel: int, addr: int, n: int) -> None:
        """Initiate an I2C multi-byte read (fire and forget — poll with read_status_query)."""
        async with self._lock:
            await _run(self._native.read_multiple_bytes, channel, addr, n)

    async def write_read_multiple_bytes(
        self, channel: int, addr: int, n: int, start_address: int
    ) -> None:
        """Initiate a write-then-read I2C transaction (fire and forget)."""
        async with self._lock:
            await _run(self._native.write_read_multiple_bytes, channel, addr, n, start_address)

    async def read_status_query(self, channel: int) -> dict:
        """Return I2C read status dict with ``i2c_transaction_status``, ``num_bytes_read``, ``bytes``."""
        async with self._lock:
            return await _run(self._native.read_status_query, channel)

    # ── Motor ─────────────────────────────────────────────────────────────

    async def set_motor_channel_mode(self, channel: int, mode: int, float_at_zero: bool) -> None:
        """Set the motor control mode."""
        async with self._lock:
            await _run(self._native.set_motor_channel_mode, channel, mode, float_at_zero)

    async def get_motor_channel_mode(self, channel: int) -> dict:
        """Return a dict with ``motor_mode`` (int) and ``float_at_zero`` (bool)."""
        async with self._lock:
            return await _run(self._native.get_motor_channel_mode, channel)

    async def set_motor_channel_enable(self, channel: int, enable: bool) -> None:
        """Enable or disable a motor channel."""
        async with self._lock:
            await _run(self._native.set_motor_channel_enable, channel, enable)

    async def get_motor_channel_enable(self, channel: int) -> bool:
        """Return True if the motor channel is enabled."""
        async with self._lock:
            return await _run(self._native.get_motor_channel_enable, channel)

    async def set_motor_channel_current_alert_level(self, channel: int, limit_ma: int) -> None:
        """Set the motor current alert threshold in milliamps."""
        async with self._lock:
            await _run(self._native.set_motor_channel_current_alert_level, channel, limit_ma)

    async def get_motor_channel_current_alert_level(self, channel: int) -> int:
        """Return the motor current alert threshold in milliamps."""
        async with self._lock:
            return await _run(self._native.get_motor_channel_current_alert_level, channel)

    async def reset_encoder(self, channel: int) -> None:
        """Reset the motor encoder to zero."""
        async with self._lock:
            await _run(self._native.reset_encoder, channel)

    async def set_motor_constant_power(self, channel: int, power: float) -> None:
        """Set constant power level [-1.0, 1.0]."""
        async with self._lock:
            await _run(self._native.set_motor_constant_power, channel, power)

    async def get_motor_constant_power(self, channel: int) -> float:
        """Return the constant power setting."""
        async with self._lock:
            return await _run(self._native.get_motor_constant_power, channel)

    async def set_motor_target_velocity(self, channel: int, velocity_cps: int) -> None:
        """Set the target velocity in counts per second."""
        async with self._lock:
            await _run(self._native.set_motor_target_velocity, channel, velocity_cps)

    async def get_motor_target_velocity(self, channel: int) -> int:
        """Return the target velocity in counts per second."""
        async with self._lock:
            return await _run(self._native.get_motor_target_velocity, channel)

    async def set_motor_target_position(
        self, channel: int, position: int, tolerance: int
    ) -> None:
        """Set the target position and tolerance in encoder counts."""
        async with self._lock:
            await _run(self._native.set_motor_target_position, channel, position, tolerance)

    async def get_motor_target_position(self, channel: int) -> dict:
        """Return a dict with ``target_position`` and ``target_tolerance``."""
        async with self._lock:
            return await _run(self._native.get_motor_target_position, channel)

    async def is_motor_at_target(self, channel: int) -> bool:
        """Return True if the motor has reached its target position."""
        async with self._lock:
            return await _run(self._native.is_motor_at_target, channel)

    async def get_encoder_position(self, channel: int) -> int:
        """Return the current encoder count."""
        async with self._lock:
            return await _run(self._native.get_encoder_position, channel)

    async def set_closed_loop_control_coefficients(
        self, channel: int, mode: int, params: dict
    ) -> None:
        """Set PID/PIDF coefficients.  ``params`` must contain ``type``, ``p``, ``i``, ``d`` and
        optionally ``f`` (required when ``type == 1``)."""
        async with self._lock:
            await _run(self._native.set_closed_loop_control_coefficients, channel, mode, params)

    async def get_closed_loop_control_coefficients(self, channel: int, mode: int) -> dict:
        """Return PID/PIDF coefficients dict."""
        async with self._lock:
            return await _run(self._native.get_closed_loop_control_coefficients, channel, mode)

    # ── Servo ─────────────────────────────────────────────────────────────

    async def set_servo_configuration(self, channel: int, frame_period: int) -> None:
        """Set the servo frame period in microseconds."""
        async with self._lock:
            await _run(self._native.set_servo_configuration, channel, frame_period)

    async def get_servo_configuration(self, channel: int) -> int:
        """Return the servo frame period in microseconds."""
        async with self._lock:
            return await _run(self._native.get_servo_configuration, channel)

    async def set_servo_pulse_width(self, channel: int, width: int) -> None:
        """Set the servo pulse width in microseconds."""
        async with self._lock:
            await _run(self._native.set_servo_pulse_width, channel, width)

    async def get_servo_pulse_width(self, channel: int) -> int:
        """Return the servo pulse width in microseconds."""
        async with self._lock:
            return await _run(self._native.get_servo_pulse_width, channel)

    async def set_servo_enable(self, channel: int, enable: bool) -> None:
        """Enable or disable a servo channel."""
        async with self._lock:
            await _run(self._native.set_servo_enable, channel, enable)

    async def get_servo_enable(self, channel: int) -> bool:
        """Return True if the servo channel is enabled."""
        async with self._lock:
            return await _run(self._native.get_servo_enable, channel)

    # ── Static ────────────────────────────────────────────────────────────

    @staticmethod
    async def discover_rev_hubs(serial: Serial) -> dict:
        """Discover all hubs on the bus and return their addresses.

        :param serial: An open :class:`Serial` port.
        :returns: Dict with ``parent_address``, ``child_addresses``, and
            ``number_of_child_modules``.
        """
        return await _run(_RevHub.discover_rev_hubs, serial.get_native())
