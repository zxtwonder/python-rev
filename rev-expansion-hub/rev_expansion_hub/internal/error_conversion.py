"""Convert low-level :class:`~rev_rhsplib.RhspLibError` exceptions to rev-core errors."""

from __future__ import annotations

from collections.abc import Callable, Awaitable
from typing import TypeVar

import rev_rhsplib as _rhsplib
from rev_core.general_errors import (
    GeneralSerialError,
    HubNotRespondingError,
    TimeoutError,
)
from rev_core.nack_errors import (
    CommandNotSupportedError,
    ParameterOutOfRangeError,
    nack_code_to_error,
)
from rev_expansion_hub.errors.rhsp_lib_error import RhspLibError

T = TypeVar("T")


def _create_error(e: Exception, serial_number: str | None) -> Exception:
    if not isinstance(e, _rhsplib.RhspLibError):
        return e

    if hasattr(e, "nack_code"):
        return nack_code_to_error(e.nack_code)

    code = e.error_code

    if code == _rhsplib.ERROR_GENERAL:
        return RhspLibError("General librhsp error")
    if code == _rhsplib.ERROR_MSG_NUMBER_MISMATCH:
        return RhspLibError("Message Number Mismatch")
    if code == _rhsplib.ERROR_NOT_OPENED:
        return RhspLibError("Hub is not opened")
    if code == _rhsplib.ERROR_COMMAND_NOT_SUPPORTED:
        return CommandNotSupportedError()
    if code == _rhsplib.ERROR_UNEXPECTED_RESPONSE:
        return RhspLibError("Unexpected packet received")
    if code == _rhsplib.ERROR_TIMEOUT:
        return TimeoutError()
    if code == _rhsplib.ERROR_NO_HUBS_DISCOVERED:
        return HubNotRespondingError(
            f"The REV Hub with serial number {serial_number} did not respond when spoken to. "
            "It may be soft-bricked and need its firmware re-installed."
        )
    if code == _rhsplib.ERROR_SERIAL:
        return GeneralSerialError(serial_number or "no serial number provided")
    if _rhsplib.ERROR_ARG5_OUT_OF_RANGE <= code <= _rhsplib.ERROR_ARG0_OUT_OF_RANGE:
        index = -code + _rhsplib.ERROR_ARG0_OUT_OF_RANGE
        return ParameterOutOfRangeError(index)

    return e


async def convert_error_async(
    serial_number: str | None,
    block: Callable[[], Awaitable[T]],
) -> T:
    """Await *block* and convert any :class:`~rev_rhsplib.RhspLibError` to a rev-core error."""
    try:
        return await block()
    except Exception as e:
        raise _create_error(e, serial_number) from None


def convert_error_sync(
    serial_number: str | None,
    block: Callable[[], T],
) -> T:
    """Call *block* and convert any :class:`~rev_rhsplib.RhspLibError` to a rev-core error."""
    try:
        return block()
    except Exception as e:
        raise _create_error(e, serial_number) from None
