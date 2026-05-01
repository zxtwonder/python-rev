"""Interface query command."""

from rev_core.expansion_hub import ExpansionHub


async def query_interface(hub: ExpansionHub, name: str) -> None:
    iface = await hub.query_interface(name)
    print(
        f"Interface: {iface.name} has {iface.number_id_values} ids, "
        f"starting at {iface.first_packet_id}"
    )
