from rev_core.nack_errors.nack_code import NackCode
from rev_core.nack_errors.nack_error import NackError


class DigitalChannelNotConfiguredForOutputError(NackError):
    """Raised when writing to a digital channel that is not configured as output."""

    def __init__(self, nack_code: int) -> None:
        channel = nack_code - NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_OUTPUT_START
        super().__init__(nack_code, f"digital channel {channel} not configured for output")
        self.digital_channel = channel


class NoDigitalChannelsConfiguredForOutputError(NackError):
    """Raised when no digital channels are configured for output."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.NO_DIGITAL_CHANNELS_CONFIGURED_FOR_OUTPUT,
            "No digital channels configured for output",
        )


class DigitalChannelNotConfiguredForInputError(NackError):
    """Raised when reading from a digital channel that is not configured as input."""

    def __init__(self, nack_code: int) -> None:
        channel = nack_code - NackCode.DIGITAL_CHANNEL_NOT_CONFIGURED_FOR_INPUT_START
        super().__init__(nack_code, f"digital channel {channel} not configured for input")
        self.digital_channel = channel


class NoDigitalChannelsConfiguredForInputError(NackError):
    """Raised when no digital channels are configured for input."""

    def __init__(self) -> None:
        super().__init__(
            NackCode.NO_DIGITAL_CHANNELS_CONFIGURED_FOR_INPUT,
            "No digital channels configured for input",
        )
