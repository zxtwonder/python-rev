from rev_core.general_errors.rev_hub_error import RevHubError


class NoExpansionHubWithAddressError(RevHubError):
    """Raised when no hub is found at the requested module address."""

    def __init__(self, serial_number: str, module_address: int) -> None:
        super().__init__(
            f"Unable to open hub with address {module_address} connected "
            f"via parent hub with serial number {serial_number}"
        )
        self.module_address = module_address
        self.serial_number = serial_number
