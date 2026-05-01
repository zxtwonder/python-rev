from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError
from rev_core.nack_errors.battery_too_low_error import BatteryTooLowError


class MotorNotFullyConfiguredError(NackError):
    """Raised when a motor command is sent before the motor is fully configured."""

    def __init__(self) -> None:
        super().__init__(NackCode.MOTOR_NOT_FULLY_CONFIGURED, "Motor is not fully configured")


class MotorCommandNotValidError(NackError):
    """Raised when the motor command is not valid for the current motor mode."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.COMMAND_NOT_VALID_FOR_SELECTED_MOTOR_MODE,
            "The motor is not in the correct mode for this command",
        )


class BatteryTooLowToRunMotorError(BatteryTooLowError):
    """Raised when the battery voltage is too low to run motors."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.BATTERY_VOLTAGE_TOO_LOW_TO_RUN_MOTOR,
            "Battery is too low to run motors",
        )
