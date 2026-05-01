from dataclasses import dataclass


@dataclass
class Rgb:
    """RGB color with components in [0, 255]."""

    red: int
    green: int
    blue: int
