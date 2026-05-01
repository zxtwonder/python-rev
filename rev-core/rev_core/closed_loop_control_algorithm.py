from enum import IntEnum


class ClosedLoopControlAlgorithm(IntEnum):
    """Closed-loop motor control algorithm.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    Pid = 0
    Pidf = 1
