from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError
from rev_core.nack_errors.battery_too_low_error import BatteryTooLowError


class ServoNotFullyConfiguredError(NackError):
    """Raised when a servo command is sent before the servo is fully configured."""

    def __init__(self) -> None:
        super().__init__(NackCode.SERVO_NOT_FULLY_CONFIGURED, "Servo is not fully configured")


class BatteryTooLowToRunServoError(BatteryTooLowError):
    """Raised when the battery voltage is too low to run servos."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.BATTERY_VOLTAGE_TOO_LOW_TO_RUN_SERVO,
            "Battery is too low to run servos",
        )
