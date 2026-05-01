from dataclasses import dataclass


@dataclass
class LedPattern:
    """A 16-step LED animation pattern stored as packed RGBT words.

    Each step encodes red, green, blue (0-255) and time (in tenths of a second)
    as a single uint32.  Use :func:`create_led_pattern` to build one from
    :class:`LedPatternStep` objects.
    """

    rgbt_pattern_step0: int = 0
    rgbt_pattern_step1: int = 0
    rgbt_pattern_step2: int = 0
    rgbt_pattern_step3: int = 0
    rgbt_pattern_step4: int = 0
    rgbt_pattern_step5: int = 0
    rgbt_pattern_step6: int = 0
    rgbt_pattern_step7: int = 0
    rgbt_pattern_step8: int = 0
    rgbt_pattern_step9: int = 0
    rgbt_pattern_step10: int = 0
    rgbt_pattern_step11: int = 0
    rgbt_pattern_step12: int = 0
    rgbt_pattern_step13: int = 0
    rgbt_pattern_step14: int = 0
    rgbt_pattern_step15: int = 0


class LedPatternStep:
    """A single step in an LED animation pattern.

    :param t: Duration of this step in seconds.
    :param r: Red component in [0, 255].
    :param g: Green component in [0, 255].
    :param b: Blue component in [0, 255].
    """

    def __init__(self, t: float, r: int, g: int, b: int) -> None:
        self.t = t
        self.r = r
        self.g = g
        self.b = b


def _encode_step(step: LedPatternStep) -> int:
    """Pack a :class:`LedPatternStep` into the hub's uint32 RGBT format."""
    return (
        ((step.r & 0xFF) << 24)
        | ((step.g & 0xFF) << 16)
        | ((step.b & 0xFF) << 8)
        | (int(step.t * 10) & 0xFF)
    )


def create_led_pattern(led_steps: list[LedPatternStep]) -> LedPattern:
    """Build a :class:`LedPattern` from up to 16 :class:`LedPatternStep` objects.

    Steps beyond index 15 are ignored.  Missing steps default to 0 (off).

    :param led_steps: Ordered list of LED steps.
    :returns: A :class:`LedPattern` ready to send to the hub.
    """

    def _get_or_zero(index: int) -> int:
        if index < len(led_steps):
            return _encode_step(led_steps[index])
        return 0

    return LedPattern(
        rgbt_pattern_step0=_get_or_zero(0),
        rgbt_pattern_step1=_get_or_zero(1),
        rgbt_pattern_step2=_get_or_zero(2),
        rgbt_pattern_step3=_get_or_zero(3),
        rgbt_pattern_step4=_get_or_zero(4),
        rgbt_pattern_step5=_get_or_zero(5),
        rgbt_pattern_step6=_get_or_zero(6),
        rgbt_pattern_step7=_get_or_zero(7),
        rgbt_pattern_step8=_get_or_zero(8),
        rgbt_pattern_step9=_get_or_zero(9),
        rgbt_pattern_step10=_get_or_zero(10),
        rgbt_pattern_step11=_get_or_zero(11),
        rgbt_pattern_step12=_get_or_zero(12),
        rgbt_pattern_step13=_get_or_zero(13),
        rgbt_pattern_step14=_get_or_zero(14),
        rgbt_pattern_step15=_get_or_zero(15),
    )
