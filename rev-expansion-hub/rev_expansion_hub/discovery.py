"""Discovery helpers for finding connected REV Expansion Hubs."""

import serial.tools.list_ports
from rev_core.expansion_hub import ParentExpansionHub
from rev_expansion_hub.open_rev_hub import open_expansion_hub_and_all_children

_FTDI_VID = "0403"
_FTDI_PID = "6015"
_EX_HUB_SERIAL_PREFIX = "DQ"


async def get_possible_expansion_hub_serial_numbers() -> list[str]:
    """Return the serial numbers of all likely Expansion Hubs detected on serial ports.

    A port is considered an Expansion Hub if its VID is ``0403``, PID is ``6015``,
    and serial number starts with ``"DQ"`` (FTDI VCP with REV-specific serial string).
    """
    results: list[str] = []
    for port in serial.tools.list_ports.comports():
        if (
            port.vid is not None
            and f"{port.vid:04X}" == _FTDI_VID
            and port.pid is not None
            and f"{port.pid:04X}" == _FTDI_PID
            and port.serial_number is not None
            and port.serial_number.startswith(_EX_HUB_SERIAL_PREFIX)
        ):
            results.append(port.serial_number)
    return results


async def open_connected_expansion_hubs() -> list[ParentExpansionHub]:
    """Open all connected REV Expansion Hubs.

    :returns: A list of parent hubs.  Child hubs are accessible via
        :attr:`~rev_core.rev_hub.ParentRevHub.children` on each parent.
    """
    serial_numbers = await get_possible_expansion_hub_serial_numbers()
    hubs: list[ParentExpansionHub] = []
    for serial_number in serial_numbers:
        hub = await open_expansion_hub_and_all_children(serial_number)
        hubs.append(hub)
    return hubs
