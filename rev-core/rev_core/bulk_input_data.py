from dataclasses import dataclass


@dataclass
class BulkInputData:
    """Snapshot of all sensor inputs read in a single hub command."""

    digital_inputs: int
    """Bit-packed digital input states (bit N = channel N)."""

    motor0_position_enc: int
    """Motor 0 encoder position in counts."""

    motor1_position_enc: int
    """Motor 1 encoder position in counts."""

    motor2_position_enc: int
    """Motor 2 encoder position in counts."""

    motor3_position_enc: int
    """Motor 3 encoder position in counts."""

    motor_status: int
    """Motor status byte."""

    motor0_velocity_cps: int
    """Motor 0 velocity in counts per second."""

    motor1_velocity_cps: int
    """Motor 1 velocity in counts per second."""

    motor2_velocity_cps: int
    """Motor 2 velocity in counts per second."""

    motor3_velocity_cps: int
    """Motor 3 velocity in counts per second."""

    analog0_mv: int
    """Analog channel 0 reading in millivolts."""

    analog1_mv: int
    """Analog channel 1 reading in millivolts."""

    analog2_mv: int
    """Analog channel 2 reading in millivolts."""

    analog3_mv: int
    """Analog channel 3 reading in millivolts."""
