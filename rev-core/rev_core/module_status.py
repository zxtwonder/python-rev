from dataclasses import dataclass


@dataclass
class ModuleStatus:
    """Status word and motor alert flags returned by GetModuleStatus."""

    status_word: int
    """Raw status word from the hub."""

    motor_alerts: int
    """Bit-packed motor alert flags."""
