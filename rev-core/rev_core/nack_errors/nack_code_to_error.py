from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError
from rev_core.nack_errors.parameter_out_of_range_error import ParameterOutOfRangeError
from rev_core.nack_errors.digital_channel_errors import (
    DigitalChannelNotConfiguredForInputError,
    DigitalChannelNotConfiguredForOutputError,
    NoDigitalChannelsConfiguredForInputError,
    NoDigitalChannelsConfiguredForOutputError,
)
from rev_core.nack_errors.i2c_errors import (
    I2cControllerBusyError,
    I2cNoResultsPendingError,
    I2cOperationInProgressError,
    I2cQueryMismatchError,
    I2cTimeoutError,
    I2cTimeoutSclStuckError,
    I2cTimeoutSdaStuckError,
)
from rev_core.nack_errors.motor_errors import (
    BatteryTooLowToRunMotorError,
    MotorCommandNotValidError,
    MotorNotFullyConfiguredError,
)
from rev_core.nack_errors.servo_errors import (
    BatteryTooLowToRunServoError,
    ServoNotFullyConfiguredError,
)
from rev_core.nack_errors.diagnostic_errors import (
    CommandImplementationPendingError,
    CommandNotSupportedError,
    CommandRoutingError,
)
from rev_core.nack_errors.unrecognized_nack_error import UnrecognizedNackError


def nack_code_to_error(nack_code: int) -> NackError:
    """Convert a raw NACK reason code to the appropriate :class:`NackError` subclass."""
    if NackCode.PARAMETER_OUT_OF_RANGE_START <= nack_code <= NackCode.PARAMETER_OUT_OF_RANGE_END:
        return ParameterOutOfRangeError(nack_code)
    if (
        NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_OUTPUT_START
        <= nack_code
        <= NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_OUTPUT_END
    ):
        return DigitalChannelNotConfiguredForOutputError(nack_code)
    if nack_code == NackCode.NO_DIGITAL_CHANNELS_CONFIGURED_FOR_OUTPUT:
        return NoDigitalChannelsConfiguredForOutputError()
    if (
        NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_INPUT_START
        <= nack_code
        <= NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_INPUT_END
    ):
        return DigitalChannelNotConfiguredForInputError(nack_code)
    if nack_code == NackCode.NO_DIGITAL_CHANNELS_CONFIGURED_FOR_INPUT:
        return NoDigitalChannelsConfiguredForInputError()
    if nack_code == NackCode.SERVO_NOT_FULLY_CONFIGURED:
        return ServoNotFullyConfiguredError()
    if nack_code == NackCode.BATTERY_VOLTAGE_TOO_LOW_TO_RUN_SERVO:
        return BatteryTooLowToRunServoError()
    if nack_code == NackCode.I2C_CONTROLLER_BUSY:
        return I2cControllerBusyError()
    if nack_code == NackCode.I2C_OPERATION_IN_PROGRESS:
        return I2cOperationInProgressError()
    if nack_code == NackCode.I2C_NO_RESULTS_PENDING:
        return I2cNoResultsPendingError()
    if nack_code == NackCode.I2C_QUERY_MISMATCH:
        return I2cQueryMismatchError()
    if nack_code == NackCode.I2C_TIMEOUT_SDA_STUCK:
        return I2cTimeoutSdaStuckError()
    if nack_code == NackCode.I2C_TIMEOUT_SCL_STUCK:
        return I2cTimeoutSclStuckError()
    if nack_code == NackCode.I2C_TIMEOUT:
        return I2cTimeoutError()
    if nack_code == NackCode.MOTOR_NOT_FULLY_CONFIGURED:
        return MotorNotFullyConfiguredError()
    if nack_code == NackCode.COMMAND_NOT_VALID_FOR_SELECTED_MOTOR_MODE:
        return MotorCommandNotValidError()
    if nack_code == NackCode.BATTERY_VOLTAGE_TOO_LOW_TO_RUN_MOTOR:
        return BatteryTooLowToRunMotorError()
    if nack_code == NackCode.COMMAND_IMPLEMENTATION_PENDING:
        return CommandImplementationPendingError()
    if nack_code == NackCode.COMMAND_ROUTING_ERROR:
        return CommandRoutingError()
    if nack_code == NackCode.COMMAND_NOT_SUPPORTED:
        return CommandNotSupportedError()
    return UnrecognizedNackError(nack_code)
