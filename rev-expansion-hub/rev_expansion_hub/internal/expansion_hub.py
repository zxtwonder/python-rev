"""Concrete asyncio implementation of :class:`~rev_core.ExpansionHub`."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from rev_rhsplib import Serial as NativeSerial, RevHub as NativeRevHub
from rev_core.bulk_input_data import BulkInputData
from rev_core.closed_loop_control_algorithm import ClosedLoopControlAlgorithm
from rev_core.debug_group import DebugGroup
from rev_core.digital_channel_direction import DigitalChannelDirection
from rev_core.digital_state import DigitalState
from rev_core.expansion_hub import ExpansionHub
from rev_core.general_errors import NoExpansionHubWithAddressError, TimeoutError
from rev_core.i2c_read_status import I2CReadStatus
from rev_core.i2c_speed_code import I2CSpeedCode
from rev_core.i2c_write_status import I2CWriteStatus
from rev_core.led_pattern import LedPattern
from rev_core.module_interface import ModuleInterface
from rev_core.module_status import ModuleStatus
from rev_core.motor_mode import MotorMode
from rev_core.nack_errors import I2cOperationInProgressError, ParameterOutOfRangeError
from rev_core.pid_coefficients import PidCoefficients
from rev_core.pidf_coefficients import PidfCoefficients
from rev_core.rev_hub import RevHub, ParentRevHub
from rev_core.rev_hub_type import RevHubType
from rev_core.rgb import Rgb
from rev_core.verbosity_level import VerbosityLevel
from rev_core.version import Version
from rev_expansion_hub.internal.error_conversion import (
    convert_error_async,
    convert_error_sync,
)


class ExpansionHubInternal(ExpansionHub):
    """Concrete implementation of :class:`~rev_core.ExpansionHub` backed by rev_rhsplib."""

    def __init__(
        self,
        is_parent: bool,
        serial_port: NativeSerial,
        serial_number: str | None = None,
    ) -> None:
        self._native_hub = NativeRevHub()
        self._hub_is_parent = is_parent
        self.serial_number = serial_number
        self.serial_port = serial_port
        self.module_address: int = 0
        self._mutable_children: list[RevHub] = []
        self._keep_alive_task: asyncio.Task | None = None
        self._error_listeners: list[Callable[[Exception], None]] = []
        self.type = RevHubType.ExpansionHub

    # ── RevHub ABC ────────────────────────────────────────────────────────────

    @property
    def module_address(self) -> int:
        return self._module_address

    @module_address.setter
    def module_address(self, value: int) -> None:
        self._module_address = value

    @property
    def type(self) -> RevHubType:
        return self._type

    @type.setter
    def type(self, value: RevHubType) -> None:
        self._type = value

    @property
    def children(self) -> tuple[RevHub, ...]:
        return tuple(self._mutable_children)

    def is_parent(self) -> bool:
        return self._hub_is_parent

    def is_expansion_hub(self) -> bool:
        return True

    def on(self, event_name: str, listener: Callable[[Exception], None]) -> RevHub:
        """Register a listener for background errors (e.g. keep-alive failures)."""
        if event_name == "error":
            self._error_listeners.append(listener)
        return self

    def emit_error(self, error: Exception) -> None:
        for listener in self._error_listeners:
            listener(error)

    # ── ExpansionHub ABC ──────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        return convert_error_sync(self.serial_number, self._native_hub.is_opened)

    @property
    def response_timeout_ms(self) -> int:
        return convert_error_sync(
            self.serial_number, self._native_hub.get_response_timeout_ms
        )

    @response_timeout_ms.setter
    def response_timeout_ms(self, timeout: int) -> None:
        convert_error_sync(
            self.serial_number,
            lambda: self._native_hub.set_response_timeout_ms(timeout),
        )

    def close(self) -> None:
        """Close this hub and release all C resources.

        Cancels the keep-alive task.  If this is a parent hub, also closes
        the serial port and all child hubs.
        """
        if self._keep_alive_task is not None:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None

        if self._hub_is_parent:
            for child in self._mutable_children:
                if child.is_expansion_hub():
                    child.close()
            from rev_expansion_hub.open_rev_hub import close_serial_port
            close_serial_port(self.serial_port)

    # ── Internal lifecycle ────────────────────────────────────────────────────

    async def open(self, dest_address: int) -> None:
        """Open the hub at *dest_address*.  Called internally by open_rev_hub."""
        self._module_address = dest_address
        await convert_error_async(
            self.serial_number,
            lambda: self._native_hub.open(self.serial_port, dest_address),
        )

    def get_dest_address(self) -> int:
        return convert_error_sync(self.serial_number, self._native_hub.get_dest_address)

    def set_dest_address(self, dest_address: int) -> None:
        convert_error_sync(
            self.serial_number,
            lambda: self._native_hub.set_dest_address(dest_address),
        )

    # ── Custom commands ───────────────────────────────────────────────────────

    async def send_write_command(
        self, packet_type_id: int, payload: list[int]
    ) -> list[int]:
        return await self._convert(
            lambda: self._native_hub.send_write_command(packet_type_id, payload)
        )

    async def send_read_command(
        self, packet_type_id: int, payload: list[int]
    ) -> list[int]:
        return await self._convert(
            lambda: self._native_hub.send_read_command(packet_type_id, payload)
        )

    # ── Module status / control ───────────────────────────────────────────────

    async def get_module_status(self, clear_status_after_response: bool) -> ModuleStatus:
        d = await self._convert(
            lambda: self._native_hub.get_module_status(clear_status_after_response)
        )
        return ModuleStatus(status_word=d["status_word"], motor_alerts=d["motor_alerts"])

    async def send_keep_alive(self) -> None:
        await self._convert(self._native_hub.send_keep_alive)

    async def send_fail_safe(self) -> None:
        await self._convert(self._native_hub.send_fail_safe)

    async def set_new_module_address(self, new_module_address: int) -> None:
        self._module_address = new_module_address
        await self._convert(
            lambda: self._native_hub.set_new_module_address(new_module_address)
        )

    async def query_interface(self, interface_name: str) -> ModuleInterface:
        d = await self._convert(
            lambda: self._native_hub.query_interface(interface_name)
        )
        return ModuleInterface(
            name=d["name"],
            first_packet_id=d["first_packet_id"],
            number_id_values=d["number_id_values"],
        )

    async def set_debug_log_level(
        self, debug_group: DebugGroup, verbosity_level: VerbosityLevel
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_debug_log_level(
                int(debug_group), int(verbosity_level)
            )
        )

    async def get_interface_packet_id(
        self, interface_name: str, function_number: int
    ) -> int:
        return await self._convert(
            lambda: self._native_hub.get_interface_packet_id(
                interface_name, function_number
            )
        )

    # ── LED ───────────────────────────────────────────────────────────────────

    async def set_module_led_color(self, red: int, green: int, blue: int) -> None:
        await self._convert(
            lambda: self._native_hub.set_module_led_color(red, green, blue)
        )

    async def get_module_led_color(self) -> Rgb:
        r, g, b = await self._convert(self._native_hub.get_module_led_color)
        return Rgb(red=r, green=g, blue=b)

    async def set_module_led_pattern(self, led_pattern: LedPattern) -> None:
        steps = [
            led_pattern.rgbt_pattern_step0,
            led_pattern.rgbt_pattern_step1,
            led_pattern.rgbt_pattern_step2,
            led_pattern.rgbt_pattern_step3,
            led_pattern.rgbt_pattern_step4,
            led_pattern.rgbt_pattern_step5,
            led_pattern.rgbt_pattern_step6,
            led_pattern.rgbt_pattern_step7,
            led_pattern.rgbt_pattern_step8,
            led_pattern.rgbt_pattern_step9,
            led_pattern.rgbt_pattern_step10,
            led_pattern.rgbt_pattern_step11,
            led_pattern.rgbt_pattern_step12,
            led_pattern.rgbt_pattern_step13,
            led_pattern.rgbt_pattern_step14,
            led_pattern.rgbt_pattern_step15,
        ]
        await self._convert(lambda: self._native_hub.set_module_led_pattern(steps))

    async def get_module_led_pattern(self) -> LedPattern:
        steps = await self._convert(self._native_hub.get_module_led_pattern)
        return LedPattern(
            rgbt_pattern_step0=steps[0],
            rgbt_pattern_step1=steps[1],
            rgbt_pattern_step2=steps[2],
            rgbt_pattern_step3=steps[3],
            rgbt_pattern_step4=steps[4],
            rgbt_pattern_step5=steps[5],
            rgbt_pattern_step6=steps[6],
            rgbt_pattern_step7=steps[7],
            rgbt_pattern_step8=steps[8],
            rgbt_pattern_step9=steps[9],
            rgbt_pattern_step10=steps[10],
            rgbt_pattern_step11=steps[11],
            rgbt_pattern_step12=steps[12],
            rgbt_pattern_step13=steps[13],
            rgbt_pattern_step14=steps[14],
            rgbt_pattern_step15=steps[15],
        )

    # ── Device control ────────────────────────────────────────────────────────

    async def get_bulk_input_data(self) -> BulkInputData:
        d = await self._convert(self._native_hub.get_bulk_input_data)
        return BulkInputData(
            digital_inputs=d["digital_inputs"],
            motor0_position_enc=d["motor0_position_enc"],
            motor1_position_enc=d["motor1_position_enc"],
            motor2_position_enc=d["motor2_position_enc"],
            motor3_position_enc=d["motor3_position_enc"],
            motor_status=d["motor_status"],
            motor0_velocity_cps=d["motor0_velocity_cps"],
            motor1_velocity_cps=d["motor1_velocity_cps"],
            motor2_velocity_cps=d["motor2_velocity_cps"],
            motor3_velocity_cps=d["motor3_velocity_cps"],
            analog0_mv=d["analog0_mv"],
            analog1_mv=d["analog1_mv"],
            analog2_mv=d["analog2_mv"],
            analog3_mv=d["analog3_mv"],
        )

    async def get_analog_input(self, channel: int) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(channel, 0))

    async def get_digital_bus_current(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(4, 0))

    async def get_i2c_current(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(5, 0))

    async def get_servo_current(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(6, 0))

    async def get_battery_current(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(7, 0))

    async def get_motor_current(self, motor_channel: int) -> int:
        if not 0 <= motor_channel <= 3:
            raise ParameterOutOfRangeError(1)
        return await self._convert(
            lambda: self._native_hub.get_adc(motor_channel + 8, 0)
        )

    async def get_battery_voltage(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(13, 0))

    async def get_5v_bus_voltage(self) -> int:
        return await self._convert(lambda: self._native_hub.get_adc(12, 0))

    async def get_temperature(self) -> float:
        deci_celsius = await self._convert(lambda: self._native_hub.get_adc(14, 0))
        return deci_celsius / 10

    async def set_phone_charge_control(self, charge_enable: bool) -> None:
        await self._convert(
            lambda: self._native_hub.phone_charge_control(charge_enable)
        )

    async def get_phone_charge_control(self) -> bool:
        return await self._convert(self._native_hub.phone_charge_query)

    async def inject_data_log_hint(self, hint_text: str) -> None:
        await self._convert(lambda: self._native_hub.inject_data_log_hint(hint_text))

    async def read_version_string(self) -> str:
        return await self._convert(self._native_hub.read_version_string)

    async def read_version(self) -> Version:
        d = await self._convert(self._native_hub.read_version)
        return Version(
            engineering_revision=d["engineering_revision"],
            minor_version=d["minor_version"],
            major_version=d["major_version"],
            minor_hw_revision=d["minor_hw_revision"],
            major_hw_revision=d["major_hw_revision"],
            hw_type=d["hw_type"],
        )

    async def set_ftdi_reset_control(self, ftdi_reset_control: bool) -> None:
        await self._convert(
            lambda: self._native_hub.ftdi_reset_control(ftdi_reset_control)
        )

    async def get_ftdi_reset_control(self) -> bool:
        return await self._convert(self._native_hub.ftdi_reset_query)

    # ── Digital I/O ───────────────────────────────────────────────────────────

    async def set_digital_output(
        self, digital_channel: int, value: DigitalState
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_single_digital_output(
                digital_channel, value.is_high()
            )
        )

    async def set_all_digital_outputs(self, bit_packed_field: int) -> None:
        await self._convert(
            lambda: self._native_hub.set_all_digital_outputs(bit_packed_field)
        )

    async def set_digital_direction(
        self, digital_channel: int, direction: DigitalChannelDirection
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_digital_direction(
                digital_channel, int(direction)
            )
        )

    async def get_digital_direction(
        self, digital_channel: int
    ) -> DigitalChannelDirection:
        value = await self._convert(
            lambda: self._native_hub.get_digital_direction(digital_channel)
        )
        return DigitalChannelDirection(value)

    async def get_digital_input(self, digital_channel: int) -> DigitalState:
        high = await self._convert(
            lambda: self._native_hub.get_single_digital_input(digital_channel)
        )
        return DigitalState.HIGH if high else DigitalState.LOW

    async def get_all_digital_inputs(self) -> int:
        return await self._convert(self._native_hub.get_all_digital_inputs)

    # ── I2C ───────────────────────────────────────────────────────────────────

    async def set_i2c_channel_configuration(
        self, i2c_channel: int, speed_code: I2CSpeedCode
    ) -> None:
        await self._convert(
            lambda: self._native_hub.configure_i2c_channel(
                i2c_channel, int(speed_code)
            )
        )

    async def get_i2c_channel_configuration(self, i2c_channel: int) -> I2CSpeedCode:
        value = await self._convert(
            lambda: self._native_hub.configure_i2c_query(i2c_channel)
        )
        return I2CSpeedCode(value)

    async def write_i2c_single_byte(
        self, i2c_channel: int, target_address: int, byte: int
    ) -> None:
        await self._convert(
            lambda: self._native_hub.write_single_byte(
                i2c_channel, target_address, byte
            )
        )

    async def write_i2c_multiple_bytes(
        self, i2c_channel: int, target_address: int, bytes: list[int]
    ) -> None:
        await self._convert(
            lambda: self._native_hub.write_multiple_bytes(
                i2c_channel, target_address, bytes
            )
        )

    async def read_i2c_single_byte(
        self, i2c_channel: int, target_address: int
    ) -> int:
        await self._convert(
            lambda: self._native_hub.read_single_byte(i2c_channel, target_address)
        )
        while True:
            try:
                status = await self._convert(
                    lambda: self._native_hub.read_status_query(i2c_channel)
                )
                return status["bytes"][0]
            except I2cOperationInProgressError:
                continue

    async def read_i2c_multiple_bytes(
        self, i2c_channel: int, target_address: int, num_bytes_to_read: int
    ) -> list[int]:
        await self._convert(
            lambda: self._native_hub.read_multiple_bytes(
                i2c_channel, target_address, num_bytes_to_read
            )
        )
        while True:
            try:
                status = await self._convert(
                    lambda: self._native_hub.read_status_query(i2c_channel)
                )
                return status["bytes"]
            except I2cOperationInProgressError:
                continue

    async def read_i2c_register(
        self,
        i2c_channel: int,
        target_address: int,
        num_bytes_to_read: int,
        register: int,
    ) -> list[int]:
        await self._convert(
            lambda: self._native_hub.write_read_multiple_bytes(
                i2c_channel, target_address, num_bytes_to_read, register
            )
        )
        while True:
            try:
                status = await self._convert(
                    lambda: self._native_hub.read_status_query(i2c_channel)
                )
                return status["bytes"]
            except I2cOperationInProgressError:
                continue

    # ── Motor ─────────────────────────────────────────────────────────────────

    async def set_motor_channel_mode(
        self, motor_channel: int, motor_mode: MotorMode, float_at_zero: bool
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_channel_mode(
                motor_channel, int(motor_mode), float_at_zero
            )
        )

    async def get_motor_channel_mode(
        self, motor_channel: int
    ) -> dict[str, MotorMode | bool]:
        d = await self._convert(
            lambda: self._native_hub.get_motor_channel_mode(motor_channel)
        )
        return {
            "motor_mode": MotorMode(d["motor_mode"]),
            "float_at_zero": d["float_at_zero"],
        }

    async def set_motor_channel_enable(
        self, motor_channel: int, enable: bool
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_channel_enable(motor_channel, enable)
        )

    async def get_motor_channel_enable(self, motor_channel: int) -> bool:
        return await self._convert(
            lambda: self._native_hub.get_motor_channel_enable(motor_channel)
        )

    async def set_motor_channel_current_alert_level(
        self, motor_channel: int, current_limit_ma: int
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_channel_current_alert_level(
                motor_channel, current_limit_ma
            )
        )

    async def get_motor_channel_current_alert_level(self, motor_channel: int) -> int:
        return await self._convert(
            lambda: self._native_hub.get_motor_channel_current_alert_level(motor_channel)
        )

    async def reset_motor_encoder(self, motor_channel: int) -> None:
        await self._convert(
            lambda: self._native_hub.reset_encoder(motor_channel)
        )

    async def set_motor_constant_power(
        self, motor_channel: int, power_level: float
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_constant_power(motor_channel, power_level)
        )

    async def get_motor_constant_power(self, motor_channel: int) -> float:
        return await self._convert(
            lambda: self._native_hub.get_motor_constant_power(motor_channel)
        )

    async def set_motor_target_velocity(
        self, motor_channel: int, velocity_cps: int
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_target_velocity(
                motor_channel, velocity_cps
            )
        )

    async def get_motor_target_velocity(self, motor_channel: int) -> int:
        return await self._convert(
            lambda: self._native_hub.get_motor_target_velocity(motor_channel)
        )

    async def set_motor_target_position(
        self,
        motor_channel: int,
        target_position_counts: int,
        target_tolerance_counts: int,
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_motor_target_position(
                motor_channel, target_position_counts, target_tolerance_counts
            )
        )

    async def get_motor_target_position(self, motor_channel: int) -> dict[str, int]:
        return await self._convert(
            lambda: self._native_hub.get_motor_target_position(motor_channel)
        )

    async def get_motor_at_target(self, motor_channel: int) -> bool:
        return await self._convert(
            lambda: self._native_hub.is_motor_at_target(motor_channel)
        )

    async def get_motor_encoder_position(self, motor_channel: int) -> int:
        return await self._convert(
            lambda: self._native_hub.get_encoder_position(motor_channel)
        )

    async def set_motor_closed_loop_control_coefficients(
        self,
        motor_channel: int,
        motor_mode: MotorMode,
        algorithm: ClosedLoopControlAlgorithm,
        pid: PidCoefficients | PidfCoefficients,
    ) -> None:
        if algorithm == ClosedLoopControlAlgorithm.Pidf:
            assert isinstance(pid, PidfCoefficients)
            params = {
                "type": int(algorithm),
                "p": pid.p,
                "i": pid.i,
                "d": pid.d,
                "f": pid.f,
            }
        else:
            params = {
                "type": int(algorithm),
                "p": pid.p,
                "i": pid.i,
                "d": pid.d,
            }
        await self._convert(
            lambda: self._native_hub.set_closed_loop_control_coefficients(
                motor_channel, int(motor_mode), params
            )
        )

    async def get_motor_closed_loop_control_coefficients(
        self, motor_channel: int, motor_mode: MotorMode
    ) -> PidfCoefficients | PidCoefficients:
        d = await self._convert(
            lambda: self._native_hub.get_closed_loop_control_coefficients(
                motor_channel, int(motor_mode)
            )
        )
        algo = ClosedLoopControlAlgorithm(d["type"])
        if algo == ClosedLoopControlAlgorithm.Pidf:
            return PidfCoefficients(p=d["p"], i=d["i"], d=d["d"], f=d["f"])
        return PidCoefficients(p=d["p"], i=d["i"], d=d["d"])

    # ── Servo ──────────────────────────────────────────────────────────────────

    async def set_servo_configuration(
        self, servo_channel: int, frame_period_us: int
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_servo_configuration(
                servo_channel, frame_period_us
            )
        )

    async def get_servo_configuration(self, servo_channel: int) -> int:
        return await self._convert(
            lambda: self._native_hub.get_servo_configuration(servo_channel)
        )

    async def set_servo_pulse_width(
        self, servo_channel: int, pulse_width_us: int
    ) -> None:
        await self._convert(
            lambda: self._native_hub.set_servo_pulse_width(servo_channel, pulse_width_us)
        )

    async def get_servo_pulse_width(self, servo_channel: int) -> int:
        return await self._convert(
            lambda: self._native_hub.get_servo_pulse_width(servo_channel)
        )

    async def set_servo_enable(self, servo_channel: int, enable: bool) -> None:
        await self._convert(
            lambda: self._native_hub.set_servo_enable(servo_channel, enable)
        )

    async def get_servo_enable(self, servo_channel: int) -> bool:
        return await self._convert(
            lambda: self._native_hub.get_servo_enable(servo_channel)
        )

    # ── Children ──────────────────────────────────────────────────────────────

    def add_child(self, hub: RevHub) -> None:
        self._mutable_children.append(hub)

    async def add_child_by_address(self, module_address: int) -> RevHub:
        """Open a child hub at *module_address* and add it to this parent.

        :raises NoExpansionHubWithAddressError: If the child does not respond.
        """
        child = ExpansionHubInternal(is_parent=False, serial_port=self.serial_port)

        try:
            await child.open(module_address)
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                try:
                    await child.send_keep_alive()
                    break
                except Exception:
                    pass
            await child.query_interface("DEKA")
        except TimeoutError:
            raise NoExpansionHubWithAddressError(
                self.serial_number or "",
                module_address,
            )

        if child.is_expansion_hub():
            from rev_expansion_hub.start_keep_alive import start_keep_alive
            start_keep_alive(child, 1000)

        self.add_child(child)
        return child

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _convert(self, block):
        """Await *block()* with error conversion, holding no extra lock (rev_rhsplib handles it)."""
        return await convert_error_async(self.serial_number, block)
