from rev_core.general_errors import RevHubError


class RhspLibError(RevHubError):
    """Raised when librhsp returns an unexpected error code with no higher-level mapping."""
