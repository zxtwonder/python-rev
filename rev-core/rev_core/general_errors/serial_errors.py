from rev_core.general_errors.rev_hub_error import RevHubError


class UnableToOpenSerialError(RevHubError):
    """Raised when the serial port cannot be opened."""

    def __init__(self, serial_port: str) -> None:
        super().__init__(f"Unable to open serial port {serial_port}")


class InvalidSerialArguments(RevHubError):
    """Raised when invalid arguments are provided to the serial port."""

    def __init__(self, serial_port: str) -> None:
        super().__init__(f"Invalid arguments for serial port {serial_port}")


class SerialConfigurationError(RevHubError):
    """Raised when the serial port cannot be configured."""

    def __init__(self, serial_port: str) -> None:
        super().__init__(f"Error configuring serial port {serial_port}")


class SerialIoError(RevHubError):
    """Raised on an I/O error on the serial port."""

    def __init__(self, serial_port: str) -> None:
        super().__init__(f"IO Error on serial port {serial_port}")


class GeneralSerialError(RevHubError):
    """Raised on an unspecified serial port error."""

    def __init__(self, serial_number: str) -> None:
        super().__init__(f"Serial Port Error for {serial_number}")
        self.serial_number = serial_number
