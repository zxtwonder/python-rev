"""Keep-alive task management for :class:`~rev_expansion_hub.internal.ExpansionHubInternal`."""

import asyncio

from rev_expansion_hub.internal.expansion_hub import ExpansionHubInternal
from rev_expansion_hub.internal.error_conversion import convert_error_async


async def _keep_alive_loop(hub: ExpansionHubInternal, interval_ms: int) -> None:
    interval_s = interval_ms / 1000
    while True:
        try:
            await convert_error_async(hub.serial_number, hub._native_hub.send_keep_alive)
        except Exception as e:
            hub.emit_error(e)
        await asyncio.sleep(interval_s)


def start_keep_alive(hub: ExpansionHubInternal, interval_ms: int) -> None:
    """Start (or restart) a periodic keep-alive task for *hub*.

    :param hub: The hub to send keep-alive packets to.
    :param interval_ms: Interval in milliseconds between keep-alive packets.
    """
    if hub._keep_alive_task is not None:
        hub._keep_alive_task.cancel()

    loop = asyncio.get_event_loop()
    hub._keep_alive_task = loop.create_task(
        _keep_alive_loop(hub, interval_ms)
    )
