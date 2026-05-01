"""LED color and pattern commands."""

from __future__ import annotations

import re

from rev_core.expansion_hub import ExpansionHub
from rev_core.led_pattern import LedPatternStep, create_led_pattern


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"#?([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", hex_str)
    if not m:
        raise ValueError(f"Invalid hex color: {hex_str!r}")
    return int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)


def _parse_step(step: str) -> LedPatternStep:
    """Parse a step string of the form ``<time><RRGGBB>``.

    Example: ``"100FF00"`` → 1 second green.
    """
    if len(step) < 6:
        raise ValueError(
            "Please pass steps in the format <time><colorHexString>, "
            "where colorHexString is in 6-character hex format."
        )
    color_str = step[-6:]
    time_str = step[:-6]
    r, g, b = _hex_to_rgb(color_str)
    t = float(time_str) if time_str else 0.0
    return LedPatternStep(t, r, g, b)


async def led_pattern(hub: ExpansionHub, args: list[str]) -> None:
    steps = [_parse_step(s) for s in args]
    steps.append(LedPatternStep(0, 0, 0, 0))
    pattern = create_led_pattern(steps)
    await hub.set_module_led_pattern(pattern)


async def led(hub: ExpansionHub, r: int, g: int, b: int) -> None:
    print(f"Setting color to {r} {g}, {b}")
    await hub.set_module_led_color(r, g, b)


async def get_led(hub: ExpansionHub) -> None:
    rgb = await hub.get_module_led_color()
    print(f"r: {rgb.red}, g: {rgb.green}, b: {rgb.blue}")


async def get_led_pattern(hub: ExpansionHub) -> None:
    pattern = await hub.get_module_led_pattern()
    steps = [
        pattern.rgbt_pattern_step0,
        pattern.rgbt_pattern_step1,
        pattern.rgbt_pattern_step2,
        pattern.rgbt_pattern_step3,
        pattern.rgbt_pattern_step4,
        pattern.rgbt_pattern_step5,
        pattern.rgbt_pattern_step6,
        pattern.rgbt_pattern_step7,
        pattern.rgbt_pattern_step8,
        pattern.rgbt_pattern_step9,
        pattern.rgbt_pattern_step10,
        pattern.rgbt_pattern_step11,
        pattern.rgbt_pattern_step12,
        pattern.rgbt_pattern_step13,
        pattern.rgbt_pattern_step14,
        pattern.rgbt_pattern_step15,
    ]
    for step in steps:
        if step == 0:
            break
        t = (step & 0xFF) * 10
        color = (step & 0xFFFFFF00) >> 8
        print(f"t: {t}, color: {color:06x}")
