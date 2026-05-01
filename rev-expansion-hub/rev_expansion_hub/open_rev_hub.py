"""Functions for opening REV Expansion Hubs over serial."""

from __future__ import annotations

import time

import serial.tools.list_ports
import rev_rhsplib as _rhsplib
from rev_core.expansion_hub import ParentExpansionHub
from rev_core.general_errors import (
    GeneralSerialError,
    InvalidSerialArguments,
    NoExpansionHubWithAddressError,
    SerialConfigurationError,
    SerialIoError,
    TimeoutError,
    UnableToOpenSerialError,
)
from rev_expansion_hub.internal.expansion_hub import ExpansionHubInternal
from rev_expansion_hub.internal.error_conversion import convert_error_async
from rev_expansion_hub.start_keep_alive import start_keep_alive

_open_serial_map: dict[str, _rhsplib.Serial] = {}
"""Maps serial port path to its open Serial object."""


async def open_parent_expansion_hub(
    serial_number: str,
    module_address: int | None = None,
) -> ParentExpansionHub:
    """Open a parent Expansion Hub by its serial number.

    Does not open any child hubs.  Call
    :meth:`~rev_core.rev_hub.ParentRevHub.add_child_by_address` to add known children.

    :param serial_number: The serial number of the Expansion Hub (starts with ``"DQ"``).
    :param module_address: The module address of the parent.  If not provided, discovery
        takes upwards of a second to find the parent address.
    :returns: The opened parent hub.
    """
    return await convert_error_async(
        serial_number,
        lambda: _open_parent_hub(serial_number, module_address),
    )


async def _open_parent_hub(
    serial_number: str,
    module_address: int | None,
) -> ParentExpansionHub:
    serial_port_path = await get_serial_port_path_for_ex_hub_serial(serial_number)

    if serial_port_path not in _open_serial_map:
        _open_serial_map[serial_port_path] = await _open_serial_port(
            serial_port_path, serial_number
        )

    serial_port = _open_serial_map[serial_port_path]

    parent_hub = ExpansionHubInternal(
        is_parent=True, serial_port=serial_port, serial_number=serial_number
    )

    if module_address is None:
        addresses = await _rhsplib.RevHub.discover_rev_hubs(serial_port)
        module_address = addresses["parent_address"]

    try:
        await parent_hub.open(module_address)
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            try:
                await parent_hub.send_keep_alive()
                break
            except Exception:
                pass
        await parent_hub.query_interface("DEKA")
    except TimeoutError:
        raise NoExpansionHubWithAddressError(serial_number, module_address)

    start_keep_alive(parent_hub, 1000)

    if parent_hub.is_parent():
        return parent_hub  # type: ignore[return-value]

    raise RuntimeError(
        f"Hub at {serial_number} with module_address {module_address} is not a parent"
    )


async def open_expansion_hub_and_all_children(
    serial_number: str,
) -> ParentExpansionHub:
    """Open a parent REV hub and all of its children.

    Determining addresses will take upwards of a second.

    :param serial_number: The serial number of the REV hub (starts with ``"DQ"``).
    """
    return await convert_error_async(
        serial_number,
        lambda: _open_hub_and_children(serial_number),
    )


async def _open_hub_and_children(serial_number: str) -> ParentExpansionHub:
    serial_port_path = await get_serial_port_path_for_ex_hub_serial(serial_number)

    if serial_port_path not in _open_serial_map:
        _open_serial_map[serial_port_path] = await _open_serial_port(
            serial_port_path, serial_number
        )

    serial_port = _open_serial_map[serial_port_path]

    discovered = await _rhsplib.RevHub.discover_rev_hubs(serial_port)
    parent_address = discovered["parent_address"]
    parent_hub = await open_parent_expansion_hub(serial_number, parent_address)

    for child_address in discovered["child_addresses"]:
        await parent_hub.add_child_by_address(child_address)

    return parent_hub


async def get_serial_port_path_for_ex_hub_serial(serial_number: str) -> str:
    """Return the port path for a hub identified by *serial_number*.

    :raises RuntimeError: If no matching port is found.
    """
    for port in serial.tools.list_ports.comports():
        if port.serial_number == serial_number:
            return port.device
    raise RuntimeError(f"Unable to find serial port for {serial_number}")


def close_serial_port(serial_port: _rhsplib.Serial) -> None:
    """Close *serial_port* and remove it from the open-ports registry.

    This is the preferred way to close a serial port — it keeps the internal
    map consistent so the same path can be reopened later.
    """
    for path, port in list(_open_serial_map.items()):
        if port is serial_port:
            del _open_serial_map[path]
            break
    serial_port.close()


async def _open_serial_port(
    port_path: str,
    serial_number: str | None,
) -> _rhsplib.Serial:
    serial = _rhsplib.Serial()
    try:
        await serial.open(
            port_path,
            460800,
            8,
            _rhsplib.SerialParity.None_,
            1,
            _rhsplib.SerialFlowControl.None_,
        )
    except _rhsplib.RhspLibError as e:
        code = e.error_code
        if code == _rhsplib.SERIAL_ERROR_ARGS:
            raise InvalidSerialArguments(port_path)
        if code == _rhsplib.SERIAL_ERROR_OPENING:
            raise UnableToOpenSerialError(port_path)
        if code == _rhsplib.SERIAL_ERROR_CONFIGURE:
            raise SerialConfigurationError(port_path)
        if code == _rhsplib.SERIAL_ERROR_IO:
            raise SerialIoError(port_path)
        raise GeneralSerialError(port_path)
    return serial
