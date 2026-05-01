from dataclasses import dataclass, field


@dataclass
class DiscoveredAddresses:
    """Hub addresses found during the discovery phase."""

    parent_address: int
    """Module address of the parent hub."""

    child_addresses: list[int] = field(default_factory=list)
    """Module addresses of all child hubs."""

    number_of_child_modules: int = 0
    """Total number of child modules discovered."""
