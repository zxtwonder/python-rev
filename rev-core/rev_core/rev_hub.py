from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Literal

from rev_core.rev_hub_type import RevHubType


class RevHub(ABC):
    """Abstract base class for all REV Hub devices."""

    @property
    @abstractmethod
    def module_address(self) -> int:
        """Module address used on the RS-485 bus."""

    @property
    @abstractmethod
    def type(self) -> RevHubType:
        """Type of this hub."""

    @abstractmethod
    def is_parent(self) -> bool:
        """Return True if this hub is a parent (has a serial port)."""

    @abstractmethod
    def is_expansion_hub(self) -> "bool":
        """Return True if this hub is an Expansion Hub."""

    @abstractmethod
    def on(
        self,
        event_name: Literal["error"],
        listener: Callable[[Exception], None],
    ) -> "RevHub":
        """Register a listener for out-of-band errors (e.g. keep-alive failures).

        :param event_name: Must be ``"error"``.
        :param listener: Callable invoked with the exception when an error occurs.
        :returns: This hub instance (for chaining).
        """

    @abstractmethod
    def close(self) -> None:
        """Release all resources held by this hub."""


class ParentRevHub(RevHub, ABC):
    """A :class:`RevHub` that owns a serial port and may have child hubs."""

    @property
    @abstractmethod
    def children(self) -> tuple["RevHub", ...]:
        """Directly-connected child hubs (not grandchildren)."""

    @property
    @abstractmethod
    def serial_number(self) -> str:
        """Serial number of the USB serial adapter (e.g. ``"DQ12345"``).."""

    @abstractmethod
    async def add_child_by_address(self, module_address: int) -> "RevHub":
        """Open a child hub at the given module address and add it to :attr:`children`.

        :param module_address: RS-485 module address of the child hub.
        :raises NoExpansionHubWithAddressError: if the address does not respond.
        """
