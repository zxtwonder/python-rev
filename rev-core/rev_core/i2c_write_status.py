from dataclasses import dataclass


@dataclass
class I2CWriteStatus:
    """Status of an I2C write transaction."""

    i2c_transaction_status: int
    """Raw I2C transaction status byte."""

    num_bytes_written: int
    """Number of bytes that were written."""
