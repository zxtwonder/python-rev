"""Motor control commands."""

from __future__ import annotations

import json

from rev_core.closed_loop_control_algorithm import ClosedLoopControlAlgorithm
from rev_core.expansion_hub import ExpansionHub
from rev_core.motor_mode import MotorMode
from rev_core.pid_coefficients import PidCoefficients
from rev_core.pidf_coefficients import PidfCoefficients


async def run_motor_constant_power(
    hub: ExpansionHub, channel: int, power: float
) -> None:
    await hub.set_motor_channel_mode(channel, MotorMode.OPEN_LOOP, True)
    await hub.set_motor_constant_power(channel, power)
    await hub.set_motor_channel_enable(channel, True)

    print(f"Mode: {await hub.get_motor_channel_mode(channel)}")
    print(f"Power: {await hub.get_motor_constant_power(channel)}")
    print(f"Enabled: {await hub.get_motor_channel_enable(channel)}")


async def run_motor_constant_velocity(
    hub: ExpansionHub, channel: int, velocity: int
) -> None:
    await hub.set_motor_channel_mode(channel, MotorMode.REGULATED_VELOCITY, True)
    await hub.set_motor_target_velocity(channel, velocity)
    await hub.set_motor_channel_enable(channel, True)

    print(f"Mode: {await hub.get_motor_channel_mode(channel)}")
    print(f"Power: {await hub.get_motor_constant_power(channel)}")
    print(f"Velocity: {await hub.get_motor_target_velocity(channel)}")
    print(f"Enabled: {await hub.get_motor_channel_enable(channel)}")


async def run_motor_to_position(
    hub: ExpansionHub,
    channel: int,
    velocity: int,
    position: int,
    tolerance: int,
) -> None:
    await hub.set_motor_channel_mode(channel, MotorMode.REGULATED_POSITION, True)
    await hub.set_motor_target_velocity(channel, velocity)
    await hub.set_motor_target_position(channel, position, tolerance)
    await hub.set_motor_channel_enable(channel, True)

    print(f"Mode: {await hub.get_motor_channel_mode(channel)}")
    print(f"Power: {await hub.get_motor_constant_power(channel)}")
    print(f"Velocity: {await hub.get_motor_target_velocity(channel)}")
    print(f"Position: {await hub.get_motor_target_position(channel)}")
    print(f"Enabled: {await hub.get_motor_channel_enable(channel)}")

    while not await hub.get_motor_at_target(channel):
        pass
    print("Motor reached target")


async def read_encoder(hub: ExpansionHub, channel: int, continuous: bool) -> None:
    while True:
        count = await hub.get_motor_encoder_position(channel)
        print(f"Encoder count is {count}")
        if not continuous:
            break


async def reset_encoder(hub: ExpansionHub, channel: int) -> None:
    await hub.reset_motor_encoder(channel)


async def set_motor_alert_level(
    hub: ExpansionHub, channel: int, current_limit_ma: int
) -> None:
    await hub.set_motor_channel_current_alert_level(channel, current_limit_ma)


async def get_motor_alert_level_ma(hub: ExpansionHub, channel: int) -> int:
    return await hub.get_motor_channel_current_alert_level(channel)


async def set_motor_regulated_velocity_pid(
    hub: ExpansionHub, channel: int, p: float, i: float, d: float
) -> None:
    await hub.set_motor_closed_loop_control_coefficients(
        channel,
        MotorMode.REGULATED_VELOCITY,
        ClosedLoopControlAlgorithm.Pid,
        PidCoefficients(p=p, i=i, d=d),
    )
    await get_motor_regulated_velocity_pidf(hub, channel)


async def set_motor_regulated_velocity_pidf(
    hub: ExpansionHub, channel: int, p: float, i: float, d: float, f: float
) -> None:
    await hub.set_motor_closed_loop_control_coefficients(
        channel,
        MotorMode.REGULATED_VELOCITY,
        ClosedLoopControlAlgorithm.Pidf,
        PidfCoefficients(p=p, i=i, d=d, f=f),
    )
    await get_motor_regulated_velocity_pidf(hub, channel)


async def get_motor_regulated_velocity_pidf(hub: ExpansionHub, channel: int) -> None:
    coeff = await hub.get_motor_closed_loop_control_coefficients(
        channel, MotorMode.REGULATED_VELOCITY
    )
    print(coeff.algorithm)
    import dataclasses
    print(json.dumps(dataclasses.asdict(coeff)))
