from dataclasses import dataclass


@dataclass
class Version:
    """Hardware and firmware version information."""

    engineering_revision: int
    minor_version: int
    major_version: int
    minor_hw_revision: int
    major_hw_revision: int
    hw_type: int
