from dataclasses import dataclass

from rev_core.closed_loop_control_algorithm import ClosedLoopControlAlgorithm


@dataclass
class PidfCoefficients:
    """PIDF (PID with feed-forward) coefficients for motor closed-loop control."""

    p: float
    """Proportional gain."""

    i: float
    """Integral gain."""

    d: float
    """Derivative gain."""

    f: float
    """Feed-forward gain."""

    algorithm: ClosedLoopControlAlgorithm = ClosedLoopControlAlgorithm.Pidf
    """Discriminator tag — always :attr:`ClosedLoopControlAlgorithm.Pidf`."""
