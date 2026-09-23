"""
Day 08 - Profitability Ratio Engine

Implements:
- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)
"""

from typing import Optional


def net_profit_margin(
    net_profit: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """Calculate Net Profit Margin (%)."""

    if net_profit is None or sales is None or sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """Calculate Operating Profit Margin (%)."""

    if operating_profit is None or sales is None or sales == 0:
        return None

    return (operating_profit / sales) * 100


def opm_cross_check(
    calculated_opm: Optional[float],
    source_opm: Optional[float],
) -> bool:
    """
    Check calculated OPM against the source OPM.

    Returns True when the difference is greater than 1 percentage point.
    """

    if calculated_opm is None or source_opm is None:
        return False

    return abs(calculated_opm - source_opm) > 1.0
def cross_check_opm(
    computed_opm: Optional[float],
    source_opm: Optional[float],
    threshold: float = 1.0,
):
    """
    Cross-check calculated OPM against source OPM.
    """

    if computed_opm is None or source_opm is None:
        return None

    difference = abs(computed_opm - source_opm)

    return {
        "mismatch": difference > threshold,
        "difference": difference,
    }


def return_on_equity(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> Optional[float]:
    """Calculate Return on Equity (ROE %)."""

    if (
        net_profit is None
        or equity_capital is None
        or reserves is None
    ):
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    ebit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
) -> Optional[float]:
    """
    Calculate Return on Capital Employed (ROCE %).

    Capital employed =
        equity capital + reserves + borrowings
    """

    if (
        ebit is None
        or equity_capital is None
        or reserves is None
        or borrowings is None
    ):
        return None

    capital_employed = (
        equity_capital + reserves + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(
    net_profit: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """Calculate Return on Assets (ROA %)."""

    if net_profit is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100
def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Debt-to-Equity = Borrowings / (Equity Capital + Reserves)

    Debt-free companies return 0.
    Invalid/non-positive equity returns None.
    """
    if borrowings == 0:
        return 0

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(debt_to_equity_value, broad_sector):
    """
    Flag high leverage when D/E > 5,
    except for Financials companies.
    """
    if debt_to_equity_value is None:
        return False

    if broad_sector == "Financials":
        return False

    return debt_to_equity_value > 5


def interest_coverage_ratio(operating_profit, other_income, interest):
    """
    ICR = (Operating Profit + Other Income) / Interest

    Debt-free companies (interest = 0) return None.
    """
    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def icr_label(interest):
    """
    Return Debt Free when interest expense is zero.
    """
    if interest == 0:
        return "Debt Free"

    return None


def icr_warning(interest_coverage):
    """
    Flag companies with ICR below 1.5.
    """
    if interest_coverage is None:
        return False

    return interest_coverage < 1.5


def net_debt(borrowings, investments):
    """
    Net Debt = Borrowings - Investments
    """
    return borrowings - investments


def asset_turnover(sales, total_assets):
    """
    Asset Turnover = Sales / Total Assets

    Returns None when sales or total_assets is missing,
    or when total_assets is zero.
    """
    if sales is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return sales / total_assets