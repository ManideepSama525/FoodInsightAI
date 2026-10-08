from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def calculate_per_100g(
    value_per_100g: float | int | str,
    portion_grams: float | int | str,
) -> float:
    """Calculate a nutrient value for a requested gram portion.

    Formula:
        value_per_100g * portion_grams / 100

    The calculation is deterministic and does not involve the LLM.
    """
    value = Decimal(str(value_per_100g))
    portion = Decimal(str(portion_grams))

    if value < 0:
        raise ValueError("value_per_100g must not be negative.")

    if portion <= 0:
        raise ValueError("portion_grams must be greater than zero.")

    result = (value * portion / Decimal("100")).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP,
    )

    return float(result)
