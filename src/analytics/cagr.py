"""
Day 10 - CAGR Engine

Handles CAGR calculations for:
- Revenue
- PAT / Net Profit
- EPS

Supported edge cases:
- Positive -> Positive
- Positive -> Negative
- Negative -> Positive
- Negative -> Negative
- Zero base
- Insufficient data
"""

from typing import Optional, Tuple


def calculate_cagr(
    start_value: Optional[float],
    end_value: Optional[float],
    years: int,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate CAGR percentage.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        (cagr_value, flag)
    """

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if years <= 0:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    if start_value > 0 and end_value > 0:
        cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
        return cagr, None

    return None, "INSUFFICIENT"


def revenue_cagr(
    start_revenue: Optional[float],
    end_revenue: Optional[float],
    years: int,
) -> Tuple[Optional[float], Optional[str]]:
    """Calculate Revenue CAGR."""
    return calculate_cagr(start_revenue, end_revenue, years)


def pat_cagr(
    start_pat: Optional[float],
    end_pat: Optional[float],
    years: int,
) -> Tuple[Optional[float], Optional[str]]:
    """Calculate PAT / Net Profit CAGR."""
    return calculate_cagr(start_pat, end_pat, years)


def eps_cagr(
    start_eps: Optional[float],
    end_eps: Optional[float],
    years: int,
) -> Tuple[Optional[float], Optional[str]]:
    """Calculate EPS CAGR."""
    return calculate_cagr(start_eps, end_eps, years)