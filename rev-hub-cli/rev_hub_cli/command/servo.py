"""Servo control command."""

from __future__ import annotations

from rev_core.expansion_hub import ExpansionHub


async def run_servo(
    hub: ExpansionHub, channel: int, pulse_width: int, frame_period: int
) -> None:
    await hub.set_servo_configuration(channel, frame_period)
    await hub.set_servo_pulse_width(channel, pulse_width)
    await hub.set_servo_enable(channel, True)
