from enum import IntEnum


class I2CSpeedCode(IntEnum):
    """I2C bus speed.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    SpeedCode100_Kbps = 0
    SpeedCode400_Kbps = 1
