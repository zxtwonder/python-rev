from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from rev_core.rev_hub import RevHub, ParentRevHub
from rev_core.bulk_input_data import BulkInputData
from rev_core.closed_loop_control_algorithm import ClosedLoopControlAlgorithm
from rev_core.debug_group import DebugGroup
from rev_core.digital_channel_direction import DigitalChannelDirection
from rev_core.digital_state import DigitalState
from rev_core.i2c_read_status import I2CReadStatus
from rev_core.i2c_speed_code import I2CSpeedCode
from rev_core.i2c_write_status import I2CWriteStatus
from rev_core.led_pattern import LedPattern
from rev_core.module_interface import ModuleInterface
from rev_core.module_status import ModuleStatus
from rev_core.motor_mode import MotorMode
from rev_core.pid_coefficients import PidCoefficients
from rev_core.pidf_coefficients import PidfCoefficients
from rev_core.rgb import Rgb
from rev_core.verbosity_level import VerbosityLevel
from rev_core.version import Version


class ExpansionHub(RevHub):
    """Abstract base class for a REV Expansion Hub.

    All I/O methods are coroutines (``async def``).  Call them with ``await``.
    """

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """True if the hub connection is currently open."""

    @property
    @abstractmethod
    def response_timeout_ms(self) -> int:
        """Response timeout in milliseconds (0 = infinite)."""

    @response_timeout_ms.setter
    @abstractmethod
    def response_timeout_ms(self, timeout: int) -> None: ...

    @abstractmethod
    def close(self) -> None:
        """Close this hub and release all resources.

        If this is a parent hub, the serial port is closed and all child hubs
        are closed as well.  Do not use this hub after calling close.
        """

    @abstractmethod
    async def send_write_command(self, packet_type_id: int, payload: list[int]) -> list[int]:
        """Send a raw write command and return the response payload.

        :param packet_type_id: Packet type ID from the protocol spec.
        :param payload: Command payload bytes.
        """

    @abstractmethod
    async def send_read_command(self, packet_type_id: int, payload: list[int]) -> list[int]:
        """Send a raw read command and return the response payload.

        :param packet_type_id: Packet type ID from the protocol spec.
        :param payload: Command payload bytes.
        """

    @abstractmethod
    async def get_module_status(self, clear_status_after_response: bool) -> ModuleStatus:
        """Request the module status word and motor alert flags.

        :param clear_status_after_response: If True, the hub clears its status after responding.
        """

    @abstractmethod
    async def send_keep_alive(self) -> None:
        """Send a keep-alive packet to prevent the hub from entering fail-safe."""

    @abstractmethod
    async def send_fail_safe(self) -> None:
        """Immediately trigger the hub fail-safe (disable all outputs)."""

    @abstractmethod
    async def set_new_module_address(self, new_module_address: int) -> None:
        """Permanently change the hub's module address.

        :param new_module_address: New RS-485 module address.
        """

    @abstractmethod
    async def query_interface(self, interface_name: str) -> ModuleInterface:
        """Query the packet ID range for a named interface.

        :param interface_name: Interface name from the protocol spec (e.g. ``"DEKA"``).
        """

    @abstractmethod
    async def set_module_led_color(self, red: int, green: int, blue: int) -> None:
        """Set the onboard RGB LED color.

        :param red: Red component in [0, 255].
        :param green: Green component in [0, 255].
        :param blue: Blue component in [0, 255].
        """

    @abstractmethod
    async def get_module_led_color(self) -> Rgb:
        """Get the current onboard RGB LED color."""

    @abstractmethod
    async def set_module_led_pattern(self, led_pattern: LedPattern) -> None:
        """Set a repeating LED animation pattern.

        :param led_pattern: 16-step pattern built with :func:`~rev_core.led_pattern.create_led_pattern`.
        """

    @abstractmethod
    async def get_module_led_pattern(self) -> LedPattern:
        """Get the current LED animation pattern."""

    @abstractmethod
    async def set_debug_log_level(
        self, debug_group: DebugGroup, verbosity_level: VerbosityLevel
    ) -> None:
        """Set the log verbosity for a specific debug group.

        :param debug_group: The subsystem to configure.
        :param verbosity_level: Desired verbosity.
        """

    @abstractmethod
    async def get_interface_packet_id(self, interface_name: str, function_number: int) -> int:
        """Return the packet type ID for a specific interface function.

        :param interface_name: Interface name from the protocol spec.
        :param function_number: Function index within the interface.
        """

    # ── Device Control ──────────────────────────────────────────────────────

    @abstractmethod
    async def get_bulk_input_data(self) -> BulkInputData:
        """Read several inputs at once in a single hub command."""

    @abstractmethod
    async def get_analog_input(self, channel: int) -> int:
        """Read the value of an analog channel in millivolts.

        :param channel: Analog channel index (0–3).
        """

    @abstractmethod
    async def get_digital_bus_current(self) -> int:
        """Read the total current through the digital I/O bus in milliamps."""

    @abstractmethod
    async def get_i2c_current(self) -> int:
        """Read the total current through all I2C buses in milliamps."""

    @abstractmethod
    async def get_servo_current(self) -> int:
        """Read the total current through all servo channels in milliamps."""

    @abstractmethod
    async def get_battery_current(self) -> int:
        """Read the total current drawn from the battery in milliamps."""

    @abstractmethod
    async def get_motor_current(self, motor_channel: int) -> int:
        """Get the current draw of a given motor channel in milliamps.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def get_battery_voltage(self) -> int:
        """Get the battery voltage in millivolts."""

    @abstractmethod
    async def get_5v_bus_voltage(self) -> int:
        """Get the 5 V rail voltage in millivolts."""

    @abstractmethod
    async def get_temperature(self) -> float:
        """Get the hub's internal temperature in degrees Celsius."""

    @abstractmethod
    async def set_phone_charge_control(self, charge_enable: bool) -> None:
        """Enable or disable the phone charging voltage on the USB port.

        :param charge_enable: True to enable charging.
        """

    @abstractmethod
    async def get_phone_charge_control(self) -> bool:
        """Return True if phone charging is currently enabled."""

    @abstractmethod
    async def inject_data_log_hint(self, hint_text: str) -> None:
        """Insert text into the UART data log stream for debugging.

        :param hint_text: Text to inject (max 100 characters).
        """

    @abstractmethod
    async def read_version_string(self) -> str:
        """Read the firmware and hardware version as a human-readable string."""

    @abstractmethod
    async def read_version(self) -> Version:
        """Read firmware and hardware version numbers."""

    @abstractmethod
    async def set_ftdi_reset_control(self, ftdi_reset_control: bool) -> None:
        """Control whether the FTDI chip resets on keep-alive timeout.

        :param ftdi_reset_control: True to enable reset on timeout.
        """

    @abstractmethod
    async def get_ftdi_reset_control(self) -> bool:
        """Return True if FTDI reset on timeout is currently enabled."""

    # ── Digital I/O ─────────────────────────────────────────────────────────

    @abstractmethod
    async def set_digital_output(self, digital_channel: int, value: DigitalState) -> None:
        """Set the output state of a digital pin.

        :param digital_channel: Digital channel index (0–7).
        :param value: :attr:`DigitalState.HIGH` or :attr:`DigitalState.LOW`.
        """

    @abstractmethod
    async def set_all_digital_outputs(self, bit_packed_field: int) -> None:
        """Set the output state of all digital pins at once.

        :param bit_packed_field: Bit field where bit N controls channel N.
        """

    @abstractmethod
    async def set_digital_direction(
        self, digital_channel: int, direction: DigitalChannelDirection
    ) -> None:
        """Configure a digital pin as input or output.

        :param digital_channel: Digital channel index (0–7).
        :param direction: :attr:`DigitalChannelDirection.Input` or ``Output``.
        """

    @abstractmethod
    async def get_digital_direction(self, digital_channel: int) -> DigitalChannelDirection:
        """Get the configured direction of a digital pin.

        :param digital_channel: Digital channel index (0–7).
        """

    @abstractmethod
    async def get_digital_input(self, digital_channel: int) -> DigitalState:
        """Read the state of a digital input pin.

        :param digital_channel: Digital channel index (0–7).
        :raises NackError: If the pin is not configured for input.
        """

    @abstractmethod
    async def get_all_digital_inputs(self) -> int:
        """Read all digital inputs as a bit-packed integer (bit N = channel N)."""

    # ── I2C ─────────────────────────────────────────────────────────────────

    @abstractmethod
    async def set_i2c_channel_configuration(
        self, i2c_channel: int, speed_code: I2CSpeedCode
    ) -> None:
        """Configure the speed of an I2C channel.

        :param i2c_channel: I2C channel index (0–3).
        :param speed_code: Desired bus speed.
        """

    @abstractmethod
    async def get_i2c_channel_configuration(self, i2c_channel: int) -> I2CSpeedCode:
        """Get the configured speed of an I2C channel.

        :param i2c_channel: I2C channel index (0–3).
        """

    @abstractmethod
    async def write_i2c_single_byte(
        self, i2c_channel: int, target_address: int, byte: int
    ) -> None:
        """Write a single byte to an I2C device.

        :param i2c_channel: I2C channel index (0–3).
        :param target_address: 7-bit slave address.
        :param byte: Byte value to write.
        """

    @abstractmethod
    async def write_i2c_multiple_bytes(
        self, i2c_channel: int, target_address: int, bytes: list[int]
    ) -> None:
        """Write multiple bytes to an I2C device.

        :param i2c_channel: I2C channel index (0–3).
        :param target_address: 7-bit slave address.
        :param bytes: Data to write.
        """

    @abstractmethod
    async def read_i2c_single_byte(self, i2c_channel: int, target_address: int) -> int:
        """Read a single byte from an I2C device.

        Initiates the read and polls until the result is available.

        :param i2c_channel: I2C channel index (0–3).
        :param target_address: 7-bit slave address.
        :returns: The byte read from the device.
        """

    @abstractmethod
    async def read_i2c_multiple_bytes(
        self, i2c_channel: int, target_address: int, num_bytes_to_read: int
    ) -> list[int]:
        """Read multiple bytes from an I2C device.

        Initiates the read and polls until the result is available.

        :param i2c_channel: I2C channel index (0–3).
        :param target_address: 7-bit slave address.
        :param num_bytes_to_read: Number of bytes to read (1–100).
        :returns: The bytes read from the device.
        """

    @abstractmethod
    async def read_i2c_register(
        self,
        i2c_channel: int,
        target_address: int,
        num_bytes_to_read: int,
        register: int,
    ) -> list[int]:
        """Write a register address then read data from an I2C device.

        :param i2c_channel: I2C channel index (0–3).
        :param target_address: 7-bit slave address.
        :param num_bytes_to_read: Number of bytes to read.
        :param register: Register address to start reading from.
        :returns: The bytes read from the device.
        """

    # ── Motor ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def set_motor_channel_mode(
        self, motor_channel: int, motor_mode: MotorMode, float_at_zero: bool
    ) -> None:
        """Configure a motor channel's control mode.

        :param motor_channel: Motor channel index (0–3).
        :param motor_mode: Desired control mode.
        :param float_at_zero: If True, motor coasts at zero. If False, it brakes.
        """

    @abstractmethod
    async def get_motor_channel_mode(
        self, motor_channel: int
    ) -> dict[str, MotorMode | bool]:
        """Get the control mode configuration for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        :returns: Dict with keys ``"motor_mode"`` (:class:`MotorMode`) and
            ``"float_at_zero"`` (:class:`bool`).
        """

    @abstractmethod
    async def set_motor_channel_enable(self, motor_channel: int, enable: bool) -> None:
        """Enable or disable a motor channel.

        :param motor_channel: Motor channel index (0–3).
        :param enable: True to enable the motor.
        """

    @abstractmethod
    async def get_motor_channel_enable(self, motor_channel: int) -> bool:
        """Return True if the motor channel is currently enabled.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def set_motor_channel_current_alert_level(
        self, motor_channel: int, current_limit_ma: int
    ) -> None:
        """Set the current alert threshold for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        :param current_limit_ma: Alert threshold in milliamps.
        """

    @abstractmethod
    async def get_motor_channel_current_alert_level(self, motor_channel: int) -> int:
        """Get the current alert threshold in milliamps for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def reset_motor_encoder(self, motor_channel: int) -> None:
        """Reset the encoder count to zero for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def set_motor_constant_power(self, motor_channel: int, power_level: float) -> None:
        """Set the constant power level for a motor (open-loop mode).

        :param motor_channel: Motor channel index (0–3).
        :param power_level: Power in the range [-1.0, 1.0].
        """

    @abstractmethod
    async def get_motor_constant_power(self, motor_channel: int) -> float:
        """Get the current constant power setting for a motor.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def set_motor_target_velocity(self, motor_channel: int, velocity_cps: int) -> None:
        """Set the target velocity for a motor (regulated velocity mode).

        :param motor_channel: Motor channel index (0–3).
        :param velocity_cps: Target velocity in encoder counts per second.
        """

    @abstractmethod
    async def get_motor_target_velocity(self, motor_channel: int) -> int:
        """Get the target velocity for a motor in counts per second.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def set_motor_target_position(
        self,
        motor_channel: int,
        target_position_counts: int,
        target_tolerance_counts: int,
    ) -> None:
        """Set the target position for a motor (regulated position mode).

        :param motor_channel: Motor channel index (0–3).
        :param target_position_counts: Target encoder count.
        :param target_tolerance_counts: Counts within which the motor is "at target".
        """

    @abstractmethod
    async def get_motor_target_position(
        self, motor_channel: int
    ) -> dict[str, int]:
        """Get the target position configuration for a motor.

        :param motor_channel: Motor channel index (0–3).
        :returns: Dict with keys ``"target_position"`` and ``"target_tolerance"`` (both int).
        """

    @abstractmethod
    async def get_motor_at_target(self, motor_channel: int) -> bool:
        """Return True if the motor has reached its target position.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def get_motor_encoder_position(self, motor_channel: int) -> int:
        """Get the current encoder count for a motor.

        :param motor_channel: Motor channel index (0–3).
        """

    @abstractmethod
    async def set_motor_closed_loop_control_coefficients(
        self,
        motor_channel: int,
        motor_mode: MotorMode,
        algorithm: ClosedLoopControlAlgorithm,
        pid: PidCoefficients | PidfCoefficients,
    ) -> None:
        """Set the closed-loop control coefficients for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        :param motor_mode: Motor mode the coefficients apply to.
        :param algorithm: :attr:`ClosedLoopControlAlgorithm.Pid` or ``Pidf``.
        :param pid: Coefficients matching the chosen algorithm.
        """

    @abstractmethod
    async def get_motor_closed_loop_control_coefficients(
        self, motor_channel: int, motor_mode: MotorMode
    ) -> PidfCoefficients | PidCoefficients:
        """Get the closed-loop control coefficients for a motor channel.

        :param motor_channel: Motor channel index (0–3).
        :param motor_mode: Motor mode to query.
        :returns: :class:`PidCoefficients` or :class:`PidfCoefficients` depending on algorithm.
        """

    # ── Servo ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def set_servo_configuration(self, servo_channel: int, frame_period_us: int) -> None:
        """Set the frame period (time between rising edges) for a servo.

        :param servo_channel: Servo channel index (0–5).
        :param frame_period_us: Frame period in microseconds.
        """

    @abstractmethod
    async def get_servo_configuration(self, servo_channel: int) -> int:
        """Get the frame period in microseconds for a servo.

        :param servo_channel: Servo channel index (0–5).
        """

    @abstractmethod
    async def set_servo_pulse_width(self, servo_channel: int, pulse_width_us: int) -> None:
        """Set the pulse width for a servo.

        :param servo_channel: Servo channel index (0–5).
        :param pulse_width_us: Pulse width in microseconds (typically 500–2500).
        """

    @abstractmethod
    async def get_servo_pulse_width(self, servo_channel: int) -> int:
        """Get the current pulse width in microseconds for a servo.

        :param servo_channel: Servo channel index (0–5).
        """

    @abstractmethod
    async def set_servo_enable(self, servo_channel: int, enable: bool) -> None:
        """Enable or disable a servo channel.

        :param servo_channel: Servo channel index (0–5).
        :param enable: True to enable the servo.
        """

    @abstractmethod
    async def get_servo_enable(self, servo_channel: int) -> bool:
        """Return True if the servo channel is currently enabled.

        :param servo_channel: Servo channel index (0–5).
        """


class ParentExpansionHub(ParentRevHub, ExpansionHub):
    """A hub that is both a :class:`ParentRevHub` and an :class:`ExpansionHub`."""
