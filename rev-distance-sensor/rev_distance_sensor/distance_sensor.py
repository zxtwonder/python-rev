"""High-level :class:`DistanceSensor` wrapper for the REV 2m Distance Sensor."""

import asyncio
from collections.abc import Callable

from rev_core.expansion_hub import ExpansionHub
from rev_distance_sensor.drivers.distance_sensor_driver import DistanceSensorDriver
from rev_distance_sensor.drivers.vl53l0x import VL53L0X


class DistanceSensor:
    """REV 2m Distance Sensor connected over I2C to an Expansion Hub.

    :param hub: The expansion hub or control hub this sensor is connected to.
    :param channel: The I2C channel the sensor is plugged into (0–3).
    """

    def __init__(self, hub: ExpansionHub, channel: int) -> None:
        self._device: DistanceSensorDriver = VL53L0X(hub, channel)
        self._task: asyncio.Task | None = None
        self._is_initialized = False

    async def setup(self) -> None:
        """Initialize the sensor.

        Must be called once before :meth:`get_distance_millimeters` or
        :meth:`start_measuring_distance`.
        """
        await self._device.setup()
        self._is_initialized = True

    async def get_distance_millimeters(self) -> int:
        """Measure the current distance in millimeters.

        :returns: Distance in mm.
        :raises RuntimeError: If :meth:`setup` has not been called.
        """
        if not self._is_initialized:
            raise RuntimeError(
                "Distance Sensor is not initialized. Please call setup() first."
            )
        return await self._device.get_distance_millimeters()

    def start_measuring_distance(
        self,
        on_distance_recorded: Callable[[int], None],
        interval: float,
    ) -> None:
        """Begin continuously recording distance measurements.

        :param on_distance_recorded: Callback invoked with each distance (mm).
        :param interval: Measurement interval in seconds.
        :raises RuntimeError: If :meth:`setup` has not been called.
        """
        if not self._is_initialized:
            raise RuntimeError(
                "Distance Sensor is not initialized. Please call setup() first."
            )
        self.stop()
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(
            self._measure_loop(on_distance_recorded, interval)
        )

    def stop(self) -> None:
        """Stop the continuous measurement task if one is running."""
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _measure_loop(
        self,
        callback: Callable[[int], None],
        interval: float,
    ) -> None:
        while True:
            distance = await self.get_distance_millimeters()
            callback(distance)
            await asyncio.sleep(interval)
