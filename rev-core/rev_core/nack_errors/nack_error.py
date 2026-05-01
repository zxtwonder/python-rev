from rev_core.general_errors.rev_hub_error import RevHubError


class NackError(RevHubError):
    """Base class for errors signalled by a NACK response from the hub."""

    def __init__(self, nack_code: int, message: str) -> None:
        super().__init__(message)
        self.nack_code = nack_code
