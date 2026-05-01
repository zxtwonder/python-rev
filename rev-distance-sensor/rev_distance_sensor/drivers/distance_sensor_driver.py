"""Abstract interface for distance sensor hardware drivers."""

from abc import ABC, abstractmethod


class DistanceSensorDriver(ABC):
    """Low-level driver interface implemented by each sensor model."""

    @abstractmethod
    async def get_distance_millimeters(self) -> int:
        """Measure distance in millimeters.

        :returns: Distance measurement in mm, or -1 on error.
        """

    @abstractmethod
    async def setup(self) -> None:
        """Initialize the sensor hardware.

        Must be called once before :meth:`get_distance_millimeters`.
        """
