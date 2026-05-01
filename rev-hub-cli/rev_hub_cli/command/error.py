"""Error-handling demonstration command."""

from __future__ import annotations

from rev_expansion_hub import (
    NackError,
    MotorNotFullyConfiguredError,
    get_possible_expansion_hub_serial_numbers,
    open_connected_expansion_hubs,
    open_parent_expansion_hub,
)


async def error() -> None:
    hubs = await open_connected_expansion_hubs()
    try:
        await hubs[0].set_motor_channel_mode(2, 1, False)  # intentionally wrong mode
        await hubs[0].set_motor_constant_power(2, 0)
        await hubs[0].set_motor_channel_enable(2, True)
        print("Expected error, but got none")
    except Exception as e:
        print(e)
        print(f"Error is:\n\t{e!r}")
        print(f"Is error a nack? {isinstance(e, NackError)}")
        if isinstance(e, NackError):
            print(f"Code is {e.nack_code}")
        print(f"Is error a motor command error? {isinstance(e, MotorNotFullyConfiguredError)}")

    hubs[0].close()

    try:
        serial_numbers = await get_possible_expansion_hub_serial_numbers()
        await open_parent_expansion_hub(serial_numbers[0], 80)
        print("Did not get error opening hub with wrong address")
    except Exception as e:
        print("Got error opening parent hub with invalid address")
        print(e)

    try:
        hubs = await open_connected_expansion_hubs()
        if hubs[0].is_parent():
            await hubs[0].add_child_by_address(95)
    except Exception as e:
        print("Got error opening child hub with invalid address")
        print(e)
    hubs[0].close()
