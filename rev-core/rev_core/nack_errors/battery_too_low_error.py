from rev_core.nack_errors.nack_error import NackError


class BatteryTooLowError(NackError):
    """Raised when the battery voltage is too low to perform the requested operation."""

    def __init__(self, nack_code: int, message: str) -> None:
        super().__init__(nack_code, message)
