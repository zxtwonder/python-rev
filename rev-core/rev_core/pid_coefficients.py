from dataclasses import dataclass

from rev_core.closed_loop_control_algorithm import ClosedLoopControlAlgorithm


@dataclass
class PidCoefficients:
    """PID coefficients for motor closed-loop control."""

    p: float
    """Proportional gain."""

    i: float
    """Integral gain."""

    d: float
    """Derivative gain."""

    algorithm: ClosedLoopControlAlgorithm = ClosedLoopControlAlgorithm.Pid
    """Discriminator tag — always :attr:`ClosedLoopControlAlgorithm.Pid`."""
