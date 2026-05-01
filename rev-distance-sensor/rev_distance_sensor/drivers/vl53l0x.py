"""VL53L0X Time-of-Flight distance sensor driver."""

from dataclasses import dataclass

from rev_core.expansion_hub import ExpansionHub
from rev_distance_sensor import registers as reg
from rev_distance_sensor.i2c_utils import (
    read_register,
    read_register_multiple_bytes,
    read_short,
    write_int,
    write_register,
    write_register_multiple_bytes,
    write_short,
)
from rev_distance_sensor.drivers.distance_sensor_driver import DistanceSensorDriver

_I2C_ADDRESS = 0x52 // 2  # 0x29


@dataclass
class _SequenceStepEnables:
    tcc: bool = False
    msrc: bool = False
    dss: bool = False
    pre_range: bool = False
    final_range: bool = False


@dataclass
class _SequenceStepTimeouts:
    pre_range_vcsel_period_pclks: int = 0
    final_range_vcsel_period_pclks: int = 0
    msrc_dss_tcc_mclks: int = 0
    pre_range_mclks: int = 0
    final_range_mclks: int = 0
    msrc_dss_tcc_us: int = 0
    pre_range_us: int = 0
    final_range_us: int = 0


class VL53L0X(DistanceSensorDriver):
    """Driver for the ST VL53L0X Time-of-Flight ranging sensor.

    Used by the REV 2m Distance Sensor accessory.
    """

    def __init__(self, hub: ExpansionHub, channel: int) -> None:
        self._hub = hub
        self._channel = channel
        self._address = _I2C_ADDRESS
        self._spad_count = 0
        self._spad_type_is_aperture = False
        self._stop_value = 0

    async def setup(self) -> None:
        """Verify the sensor and run full initialization.

        :raises RuntimeError: If no valid 2m distance sensor is found on the channel.
        """
        if not await self.is_2m_distance_sensor():
            raise RuntimeError(
                f"I2C device on channel {self._channel} is not a valid 2m Distance sensor"
            )
        await self._initialize()

    async def is_2m_distance_sensor(self) -> bool:
        """Return True if the sensor at the configured address identifies as a REV 2m sensor."""
        try:
            if await self._read_register(0xC0) != 0xEE:
                return False
            if await self._read_register(0xC1) != 0xAA:
                return False
            if await self._read_register(0xC2) != 0x10:
                return False
            if await self._read_register(0x61) != 0x00:
                return False
            return True
        except Exception:
            return False

    async def get_distance_millimeters(self) -> int:
        """Read the current distance measurement.

        :returns: Distance in millimeters, or -1 on error.
        """
        try:
            distance = await self._read_short(reg.RESULT_RANGE_STATUS + 10)
            await self._write_register(reg.SYSTEM_INTERRUPT_CLEAR, 0x01)
            return distance
        except Exception:
            return -1

    async def close(self) -> None:
        """Release the stop variable stored in the sensor.

        After calling this the physical sensor must be power-cycled before a
        new :class:`VL53L0X` instance can initialize.
        """
        await self._write_register(reg.SYS_RANGE_START, 0x01)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x00)
        await self._write_register(0x91, 0x00)
        await self._write_register(0x00, 0x01)
        await self._write_register(0xFF, 0x00)

    # ── Private initialization ─────────────────────────────────────────────

    async def _init_data(self) -> None:
        await self._write_register(0x88, 0x00)
        await self._write_register(0x80, 0x01)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x00)
        self._stop_value = await self._read_register(0x91)
        await self._write_register(0x00, 0x01)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x80, 0x00)

    async def _load_tuning_settings(self) -> None:
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x00)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x09, 0x00)
        await self._write_register(0x10, 0x00)
        await self._write_register(0x11, 0x00)
        await self._write_register(0x24, 0x01)
        await self._write_register(0x25, 0xFF)
        await self._write_register(0x75, 0x00)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x4E, 0x2C)
        await self._write_register(0x48, 0x00)
        await self._write_register(0x30, 0x20)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x30, 0x09)
        await self._write_register(0x54, 0x00)
        await self._write_register(0x31, 0x04)
        await self._write_register(0x32, 0x03)
        await self._write_register(0x40, 0x83)
        await self._write_register(0x46, 0x25)
        await self._write_register(0x60, 0x00)
        await self._write_register(0x27, 0x00)
        await self._write_register(0x50, 0x06)
        await self._write_register(0x51, 0x00)
        await self._write_register(0x52, 0x96)
        await self._write_register(0x56, 0x08)
        await self._write_register(0x57, 0x30)
        await self._write_register(0x61, 0x00)
        await self._write_register(0x62, 0x00)
        await self._write_register(0x64, 0x00)
        await self._write_register(0x65, 0x00)
        await self._write_register(0x66, 0xA0)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x22, 0x32)
        await self._write_register(0x47, 0x14)
        await self._write_register(0x49, 0xFF)
        await self._write_register(0x4A, 0x00)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x7A, 0x0A)
        await self._write_register(0x7B, 0x00)
        await self._write_register(0x78, 0x21)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x23, 0x34)
        await self._write_register(0x42, 0x00)
        await self._write_register(0x44, 0xFF)
        await self._write_register(0x45, 0x26)
        await self._write_register(0x46, 0x05)
        await self._write_register(0x40, 0x40)
        await self._write_register(0x0E, 0x06)
        await self._write_register(0x20, 0x1A)
        await self._write_register(0x43, 0x40)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x34, 0x03)
        await self._write_register(0x35, 0x44)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x31, 0x04)
        await self._write_register(0x4B, 0x09)
        await self._write_register(0x4C, 0x05)
        await self._write_register(0x4D, 0x04)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x44, 0x00)
        await self._write_register(0x45, 0x20)
        await self._write_register(0x47, 0x08)
        await self._write_register(0x48, 0x28)
        await self._write_register(0x67, 0x00)
        await self._write_register(0x70, 0x04)
        await self._write_register(0x71, 0x01)
        await self._write_register(0x72, 0xFE)
        await self._write_register(0x76, 0x00)
        await self._write_register(0x77, 0x00)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x0D, 0x01)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x80, 0x01)
        await self._write_register(0x01, 0xF8)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x8E, 0x01)
        await self._write_register(0x00, 0x01)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x80, 0x00)

    async def _initialize(self) -> None:
        await self._init_data()

        msrc_config = (await self._read_register(reg.MSRC_CONFIG_CONTROL)) | 0x12
        await self._write_register(reg.MSRC_CONFIG_CONTROL, msrc_config)

        await self._set_signal_rate_limit(0.25)
        await self._write_register(reg.SYSTEM_SEQUENCE_CONFIG, 0xFF)
        await self._get_spad_info()

        ref_spad_map = await self._read_multiple_bytes(
            reg.GLOBAL_CONFIG_SPAD_ENABLES_REF_0, 6
        )

        await self._write_register(0xFF, 0x01)
        await self._write_register(reg.DYNAMIC_SPAD_REF_EN_START_OFFSET, 0x00)
        await self._write_register(reg.DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD, 0x2C)
        await self._write_register(0xFF, 0x00)
        await self._write_register(reg.GLOBAL_CONFIG_REF_EN_START_SELECT, 0xB4)

        first_spad_to_enable = 12 if self._spad_type_is_aperture else 0
        spads_enabled = 0

        for i in range(48):
            map_index = i // 8
            if i < first_spad_to_enable or spads_enabled == self._spad_count:
                ref_spad_map[map_index] &= ~(1 << (i % 8))
            elif (ref_spad_map[map_index] >> (i % 8)) & 0x1:
                spads_enabled += 1

        await self._write_multiple_bytes(reg.GLOBAL_CONFIG_SPAD_ENABLES_REF_0, ref_spad_map)
        await self._load_tuning_settings()

        await self._write_register(reg.SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        gpio_val = await self._read_register(reg.GPIO_HV_MUX_ACTIVE_HIGH)
        await self._write_register(reg.GPIO_HV_MUX_ACTIVE_HIGH, gpio_val & ~0x10)
        await self._write_register(reg.SYSTEM_INTERRUPT_CLEAR, 0x01)

        await self._write_register(reg.SYSTEM_SEQUENCE_CONFIG, 0xE8)
        await self._write_register(reg.SYSTEM_SEQUENCE_CONFIG, 0x01)
        await self._perform_calibration(0x40)
        await self._write_register(reg.SYSTEM_SEQUENCE_CONFIG, 0x02)
        await self._perform_calibration(0x00)
        await self._write_register(reg.SYSTEM_SEQUENCE_CONFIG, 0xE8)

        await self._start_continuous(0)

    async def _start_continuous(self, period_ms: int = 0) -> None:
        await self._write_register(0x80, 0x01)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x00)
        await self._write_register(0x91, self._stop_value)
        await self._write_register(0x00, 0x01)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x80, 0x00)

        if period_ms != 0:
            calibrate_value = await self._read_short(0xF8)
            if calibrate_value != 0:
                period_ms *= calibrate_value
            await self._write_int(0x04, period_ms)
            await self._write_register(reg.SYS_RANGE_START, 0x04)
        else:
            await self._write_register(reg.SYS_RANGE_START, 0x02)

    async def _perform_calibration(self, input_val: int) -> bool:
        await self._write_register(reg.SYS_RANGE_START, 0x01 | input_val)
        await self._write_register(0x0B, 0x01)
        await self._write_register(reg.SYS_RANGE_START, 0x00)
        return True

    async def _get_spad_info(self) -> None:
        await self._write_register(0x80, 0x01)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x00)
        await self._write_register(0xFF, 0x06)
        await self._write_register(0x83, (await self._read_register(0x83)) | 0x04)
        await self._write_register(0xFF, 0x07)
        await self._write_register(0x81, 0x01)
        await self._write_register(0x80, 0x01)
        await self._write_register(0x94, 0x6B)
        await self._write_register(0x83, 0x00)

        while await self._read_register(0x83) == 0:
            pass

        await self._write_register(0x83, 0x01)
        tmp = await self._read_register(0x92)
        self._spad_count = tmp & 0x7F
        self._spad_type_is_aperture = bool((tmp >> 7) & 0x01)

        await self._write_register(0x81, 0x00)
        await self._write_register(0xFF, 0x06)
        value = await self._read_register(0x83)
        await self._write_register(0x83, value & 0xFB)
        await self._write_register(0xFF, 0x01)
        await self._write_register(0x00, 0x01)
        await self._write_register(0xFF, 0x00)
        await self._write_register(0x80, 0x00)

    async def _set_signal_rate_limit(self, mcps: float) -> None:
        await self._write_short(
            reg.FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT,
            int(mcps * (1 << 7)),
        )

    async def _get_sequence_step_enables(self) -> _SequenceStepEnables:
        config = await self._read_register(reg.SYSTEM_SEQUENCE_CONFIG)
        return _SequenceStepEnables(
            tcc=bool((config >> 4) & 0x1),
            dss=bool((config >> 3) & 0x1),
            msrc=bool((config >> 2) & 0x1),
            pre_range=bool((config >> 6) & 0x1),
            final_range=bool((config >> 7) & 0x1),
        )

    async def _get_sequence_step_timeouts(
        self, enables: _SequenceStepEnables
    ) -> _SequenceStepTimeouts:
        result = _SequenceStepTimeouts()

        result.pre_range_vcsel_period_pclks = self._decode_vcsel_period(
            await self._read_register(reg.PRE_RANGE_CONFIG_VCSEL_PERIOD)
        )
        result.msrc_dss_tcc_mclks = (
            await self._read_register(reg.MSRC_CONFIG_TIMEOUT_MACROP)
        ) + 1
        result.msrc_dss_tcc_us = self._timeout_mclks_to_microseconds(
            result.msrc_dss_tcc_mclks, result.pre_range_vcsel_period_pclks
        )
        result.pre_range_mclks = self._decode_timeout(
            await self._read_short(reg.PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI)
        )
        result.pre_range_us = self._timeout_mclks_to_microseconds(
            result.pre_range_mclks, result.pre_range_vcsel_period_pclks
        )
        result.final_range_vcsel_period_pclks = self._decode_vcsel_period(
            await self._read_register(reg.FINAL_RANGE_CONFIG_VCSEL_PERIOD)
        )
        result.final_range_mclks = self._decode_timeout(
            await self._read_short(reg.FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI)
        )
        if enables.pre_range:
            result.final_range_mclks -= result.pre_range_mclks
        result.final_range_us = self._timeout_mclks_to_microseconds(
            result.final_range_mclks, result.final_range_vcsel_period_pclks
        )
        return result

    def _encode_timeout(self, mclks: int) -> int:
        if mclks > 0:
            lsb = mclks - 1
            msb = 0
            while (lsb & 0xFFFFFF00) > 0:
                lsb >>= 1
                msb += 1
            return (msb << 8) | (lsb & 0xFF)
        return 0

    def _decode_timeout(self, value: int) -> int:
        return ((value & 0x00FF) << ((value & 0xFF00) >> 8)) + 1

    def _decode_vcsel_period(self, value: int) -> int:
        return (value + 1) << 1

    def _timeout_mclks_to_microseconds(
        self, timeout_period_mclks: int, vcsel_period_pclks: int
    ) -> int:
        macro_period = self._calc_macro_period(vcsel_period_pclks)
        return (timeout_period_mclks * macro_period + macro_period // 2) // 1000

    def _calc_macro_period(self, vcsel_period_pclks: int) -> int:
        return (2304 * vcsel_period_pclks * 1655 + 500) // 1000

    # ── I2C shorthands ────────────────────────────────────────────────────

    async def _read_register(self, register: int) -> int:
        return await read_register(self._hub, self._channel, self._address, register)

    async def _read_multiple_bytes(self, register: int, n: int) -> list[int]:
        return await read_register_multiple_bytes(
            self._hub, self._channel, self._address, register, n
        )

    async def _write_multiple_bytes(self, register: int, values: list[int]) -> None:
        await write_register_multiple_bytes(
            self._hub, self._channel, self._address, register, values
        )

    async def _write_register(self, register: int, value: int) -> None:
        await write_register(self._hub, self._channel, self._address, register, value)

    async def _write_short(self, register: int, value: int) -> None:
        await write_short(self._hub, self._channel, self._address, register, value)

    async def _read_short(self, register: int) -> int:
        return await read_short(self._hub, self._channel, self._address, register)

    async def _write_int(self, register: int, value: int) -> None:
        await write_int(self._hub, self._channel, self._address, register, value)
