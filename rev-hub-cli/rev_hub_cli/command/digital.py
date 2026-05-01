"""Digital I/O commands."""

from rev_core.digital_channel_direction import DigitalChannelDirection
from rev_core.digital_state import DigitalState
from rev_core.expansion_hub import ExpansionHub


async def digital_read(hub: ExpansionHub, channel: int, continuous: bool) -> None:
    while True:
        state = await hub.get_digital_input(channel)
        print(str(state))
        if not continuous:
            break


async def digital_write(
    hub: ExpansionHub, channel: int, state: DigitalState
) -> None:
    await hub.set_digital_direction(channel, DigitalChannelDirection.Output)
    await hub.set_digital_output(channel, state)


async def digital_read_all(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        inputs = await hub.get_all_digital_inputs()
        print(f"Digital Pins: {inputs:08b}")
        if not continuous:
            break


async def digital_write_all(
    hub: ExpansionHub, bitfield: int, bitmask: int
) -> None:
    for i in range(8):
        if (bitmask >> i) & 1:
            await hub.set_digital_direction(i, DigitalChannelDirection.Output)
        else:
            await hub.set_digital_direction(i, DigitalChannelDirection.Input)
    await hub.set_all_digital_outputs(bitfield)
