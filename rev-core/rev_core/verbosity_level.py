from enum import IntEnum


class VerbosityLevel(IntEnum):
    """Verbosity level for debug logging.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    Off = 0
    Level1 = 1
    Level2 = 2
    Level3 = 3
