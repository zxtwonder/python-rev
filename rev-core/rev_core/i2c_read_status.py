from dataclasses import dataclass, field


@dataclass
class I2CReadStatus:
    """Status of an I2C read transaction."""

    i2c_transaction_status: int
    """Raw I2C transaction status byte."""

    num_bytes_read: int
    """Number of bytes that were read."""

    bytes: list[int] = field(default_factory=list)
    """Bytes that were read from the I2C device."""
