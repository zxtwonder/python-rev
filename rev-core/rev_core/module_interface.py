from dataclasses import dataclass


@dataclass
class ModuleInterface:
    """Description of a module interface returned by a query."""

    name: str
    """Interface name string."""

    first_packet_id: int
    """Packet ID for the first function in this interface."""

    number_id_values: int
    """Number of packet ID values allocated to this interface."""
