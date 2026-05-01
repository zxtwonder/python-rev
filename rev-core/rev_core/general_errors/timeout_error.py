from rev_core.general_errors.rev_hub_error import RevHubError


class TimeoutError(RevHubError):
    """Raised when the hub does not respond within the configured timeout."""

    def __init__(self) -> None:
        super().__init__("Response timeout")
