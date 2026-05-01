"""Convert low-level :class:`~rev_rhsplib.RhspLibError` exceptions to rev-core errors."""

from collections.abc import Callable, Awaitable
from typing import TypeVar

from rev_rhsplib import RhspLibNativeError, RhspLibErrorCode
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
    if not isinstance(e, RhspLibNativeError):
        return e

    if e.nack_code is not None:
        return nack_code_to_error(e.nack_code)

    code = e.error_code

    if code == RhspLibErrorCode.GENERAL_ERROR:
        return RhspLibError("General librhsp error")
    if code == RhspLibErrorCode.MSG_NUMBER_MISMATCH:
        return RhspLibError("Message Number Mismatch")
    if code == RhspLibErrorCode.NOT_OPENED:
        return RhspLibError("Hub is not opened")
    if code == RhspLibErrorCode.COMMAND_NOT_SUPPORTED:
        return CommandNotSupportedError()
    if code == RhspLibErrorCode.UNEXPECTED_RESPONSE:
        return RhspLibError("Unexpected packet received")
    if code == RhspLibErrorCode.TIMEOUT:
        return TimeoutError()
    if code == RhspLibErrorCode.NO_HUBS_DISCOVERED:
        return HubNotRespondingError(
            f"The REV Hub with serial number {serial_number} did not respond when spoken to. "
            "It may be soft-bricked and need its firmware re-installed."
        )
    if code == RhspLibErrorCode.SERIAL_ERROR:
        return GeneralSerialError(serial_number or "no serial number provided")
    if RhspLibErrorCode.ARG_OUT_OF_RANGE_END <= code <= RhspLibErrorCode.ARG_OUT_OF_RANGE_START:
        index = -code + int(RhspLibErrorCode.ARG_OUT_OF_RANGE_START)
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
