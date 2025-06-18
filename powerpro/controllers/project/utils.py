# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Literal


def get_duration_in_minutes(duration: float = 30, measurement: Literal["in Minutes", "in Hours", "in Days"] = "in Minutes") -> float:
    """
    Converts a given duration to minutes based on the specified measurement unit.

    Args:
        duration (float, optional): The duration value to convert. Defaults to 30.
        measurement (Literal["in Minutes", "in Hours", "in Days"], optional): 
            The unit of the duration. Can be "in Minutes", "in Hours", or "in Days". 
            Defaults to "in Minutes".

    Returns:
        float: The duration converted to minutes.

    Notes:
        - If duration is not provided or is falsy, defaults to 30 minutes.
        - If measurement is not provided, defaults to "in Minutes".
    """
    if not duration:
        duration = 30 # default duration
        measurement = "in Minutes"

    if measurement == "in Minutes":
        return duration

    if measurement == "in Hours":
        return duration * 60

    if measurement == "in Days":
        return duration * 60 * 24

    raise ValueError(f"Invalid measurement unit: {measurement}. Must be one of 'in Minutes', 'in Hours', or 'in Days'.")
