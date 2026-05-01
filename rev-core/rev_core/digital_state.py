class DigitalState:
    """Represents the logical state of a digital I/O pin."""

    HIGH: "DigitalState"
    LOW: "DigitalState"

    def __init__(self, state: bool) -> None:
        self._state = state

    def is_high(self) -> bool:
        """Return True if the pin state is HIGH."""
        return self._state

    def is_low(self) -> bool:
        """Return True if the pin state is LOW."""
        return not self._state

    def __bool__(self) -> bool:
        return self._state

    def __repr__(self) -> str:
        return "DigitalState.HIGH" if self._state else "DigitalState.LOW"

    def __str__(self) -> str:
        return "High" if self._state else "Low"


DigitalState.HIGH = DigitalState(True)
DigitalState.LOW = DigitalState(False)
