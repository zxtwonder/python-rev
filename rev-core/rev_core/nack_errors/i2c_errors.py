from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError


class I2cControllerBusyError(NackError):
    """Raised when the I2C controller is already busy."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_CONTROLLER_BUSY, "I2C Controller busy")


class I2cOperationInProgressError(NackError):
    """Raised when an I2C operation is still in progress."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_OPERATION_IN_PROGRESS, "I2C Operation in progress")


class I2cNoResultsPendingError(NackError):
    """Raised when no I2C results are pending."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_NO_RESULTS_PENDING, "No I2C results pending")


class I2cQueryMismatchError(NackError):
    """Raised on an I2C query mismatch."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_QUERY_MISMATCH, "I2C query mismatch")


class I2cTimeoutSdaStuckError(NackError):
    """Raised when the I2C SDA pin is stuck."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_TIMEOUT_SDA_STUCK, "I2C SDA pin stuck")


class I2cTimeoutSclStuckError(NackError):
    """Raised when the I2C SCL pin is stuck."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_TIMEOUT_SCL_STUCK, "I2C SCL pin stuck")


class I2cTimeoutError(NackError):
    """Raised when an I2C operation times out."""

    def __init__(self) -> None:
        super().__init__(NackCode.I2C_TIMEOUT, "I2C timeout")
