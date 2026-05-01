from enum import IntEnum


class DebugGroup(IntEnum):
    """Debug group for log level configuration.

    These MUST be ordered so that their numeric values match the values
    specified in the REV Hub Serial Protocol spec.
    """

    Main = 1
    TransmitterToHost = 2
    ReceiverFromHost = 3
    ADC = 4
    PWMAndServo = 5
    ModuleLED = 6
    DigitalIO = 7
    I2C = 8
    Motor0 = 9
    Motor1 = 10
    Motor2 = 11
    Motor3 = 12
