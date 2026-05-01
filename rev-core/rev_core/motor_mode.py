from enum import IntEnum


class MotorMode(IntEnum):
    """Motor control mode.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    OPEN_LOOP = 0
    """Controls the motor's speed by setting the PWM duty cycle.
    Does not require an encoder.
    """

    REGULATED_VELOCITY = 1
    """Uses the encoder to regulate the velocity of the motor.
    Requires an encoder to be connected.
    """

    REGULATED_POSITION = 2
    """Uses an encoder to regulate the position of the motor.
    Requires an encoder to be connected.
    """
