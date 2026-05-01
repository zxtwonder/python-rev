from rev_core.general_errors.rev_hub_error import RevHubError


class HubNotRespondingError(RevHubError):
    """Raised when a hub fails to respond, possibly due to firmware issues."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
