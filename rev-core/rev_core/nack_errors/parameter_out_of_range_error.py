from rev_core.nack_errors.nack_error import NackError


class ParameterOutOfRangeError(NackError):
    """Raised when a command parameter is outside the allowed range."""

    def __init__(self, nack_code: int) -> None:
        super().__init__(nack_code, f"Parameter {nack_code} is out of range")
        self.parameter_index = nack_code
        """Zero-indexed position of the out-of-range parameter."""
