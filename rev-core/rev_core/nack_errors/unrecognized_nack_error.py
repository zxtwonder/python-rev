from rev_core.nack_errors.nack_error import NackError


class UnrecognizedNackError(NackError):
    """Raised when the hub returns an unrecognized NACK code."""

    def __init__(self, nack_code: int) -> None:
        super().__init__(
            nack_code,
            f"Received unrecognized NACK error code {nack_code} from the REV Hub",
        )
