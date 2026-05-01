from enum import IntEnum


class DigitalChannelDirection(IntEnum):
    """Direction of a digital I/O channel.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    Input = 0
    Output = 1
