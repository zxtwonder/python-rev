from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError


class CommandImplementationPendingError(NackError):
    """Raised when the command has not finished being implemented in this firmware."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.COMMAND_IMPLEMENTATION_PENDING,
            "This command has not finished being implemented in this firmware version",
        )


class CommandRoutingError(NackError):
    """Raised when the firmware reports a command routing error."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.COMMAND_ROUTING_ERROR,
            "The firmware reported a Command Routing Error",
        )


class CommandNotSupportedError(NackError):
    """Raised when the packet type ID is not recognised by the hub."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.COMMAND_NOT_SUPPORTED,
            "Command is not supported. Unknown Packet Type ID",
        )
