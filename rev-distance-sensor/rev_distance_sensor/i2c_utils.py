"""I2C read/write helpers operating on a :class:`~rev_core.ExpansionHub`."""

from rev_core.expansion_hub import ExpansionHub


async def read_register(
    hub: ExpansionHub, channel: int, address: int, register: int
) -> int:
    """Read one byte from *register* on an I2C device.

    :param hub: The expansion hub.
    :param channel: I2C channel index (0–3).
    :param address: 7-bit device address.
    :param register: Register address to read.
    :returns: The byte value.
    """
    return (await hub.read_i2c_register(channel, address, 1, register))[0]


async def read_register_multiple_bytes(
    hub: ExpansionHub, channel: int, address: int, register: int, n: int
) -> list[int]:
    """Read *n* bytes starting at *register* from an I2C device.

    :param hub: The expansion hub.
    :param channel: I2C channel index (0–3).
    :param address: 7-bit device address.
    :param register: Starting register address.
    :param n: Number of bytes to read.
    :returns: List of byte values.
    """
    return await hub.read_i2c_register(channel, address, n, register)


async def write_register(
    hub: ExpansionHub, channel: int, address: int, register: int, value: int
) -> None:
    """Write one byte to *register* on an I2C device.

    :param hub: The expansion hub.
    :param channel: I2C channel index (0–3).
    :param address: 7-bit device address.
    :param register: Register address to write.
    :param value: Byte value to write.
    """
    await hub.write_i2c_multiple_bytes(channel, address, [register, value])


async def write_register_multiple_bytes(
    hub: ExpansionHub, channel: int, address: int, register: int, values: list[int]
) -> None:
    """Write multiple bytes starting at *register* on an I2C device.

    :param hub: The expansion hub.
    :param channel: I2C channel index (0–3).
    :param address: 7-bit device address.
    :param register: Starting register address.
    :param values: Byte values to write.
    """
    await hub.write_i2c_multiple_bytes(channel, address, [register, *values])


async def read_short(
    hub: ExpansionHub, channel: int, address: int, register: int
) -> int:
    """Read a big-endian 16-bit unsigned integer from *register*.

    :returns: 16-bit value.
    """
    b = await read_register_multiple_bytes(hub, channel, address, register, 2)
    return (b[0] << 8) | b[1]


async def write_short(
    hub: ExpansionHub, channel: int, address: int, register: int, value: int
) -> None:
    """Write a big-endian 16-bit unsigned integer to *register*."""
    await write_register_multiple_bytes(
        hub, channel, address, register,
        [(value >> 8) & 0xFF, value & 0xFF],
    )


async def write_int(
    hub: ExpansionHub, channel: int, address: int, register: int, value: int
) -> None:
    """Write a big-endian 32-bit unsigned integer to *register*."""
    await hub.write_i2c_multiple_bytes(
        channel,
        address,
        [
            register,
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ],
    )
