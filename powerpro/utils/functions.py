# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import math

__all__ = (
    "round_to_nearest_eighth",
    "round_to_nearest_sixteenth",
)


def round_to_nearest_eighth(value: float) -> float:
    """
    Rounds the given value to the nearest eighth (1/8).
    Args:
        value (float): The value to be rounded.
    Returns:
        float: The value rounded to the nearest eighth.
    """
    if not value and value != 0:
        return 0.000

    # round to 3 digits
    rounded = round(value, 3)

    factor = 0.125
    
    # convert 1/8 to decimal (0.125) and round to the nearest 1/8
    return math.ceil(rounded / factor) * factor


def round_to_nearest_sixteenth(value: float) -> float:
    """
    Rounds the given value to the nearest sixteenth (1/16).
    Args:
        value (float): The value to be rounded.
    Returns:
        float: The value rounded to the nearest sixteenth.
    """
    if not value and value != 0:
        return 0.000

    # round to 4 digits
    rounded = round(value, 4)

    factor = 0.0625

    # convert 1/16 to decimal (0.0625) and round to the nearest 1/16
    return math.ceil(rounded / factor) * factor
