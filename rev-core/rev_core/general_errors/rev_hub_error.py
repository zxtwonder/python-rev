class RevHubError(Exception):
    """Base exception for all REV Hub errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
