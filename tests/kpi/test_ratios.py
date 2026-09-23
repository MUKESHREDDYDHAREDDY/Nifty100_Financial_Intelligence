import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_cross_check,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning,
)
# ============================================================
# NET PROFIT MARGIN
# ============================================================

def test_net_profit_margin_normal():
    assert net_profit_margin(100, 1000) == 10.0


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


# ============================================================
# OPERATING PROFIT MARGIN
# ============================================================

def test_operating_profit_margin_normal():
    assert operating_profit_margin(200, 1000) == 20.0


def test_opm_cross_check_no_mismatch():
    calculated = operating_profit_margin(200, 1000)

    assert opm_cross_check(calculated, 20.5) is False


def test_opm_cross_check_mismatch():
    calculated = operating_profit_margin(200, 1000)

    assert opm_cross_check(calculated, 22.0) is True


# ============================================================
# RETURN ON EQUITY
# ============================================================

def test_roe_normal():
    assert return_on_equity(100, 20, 480) == 20.0


def test_roe_negative_equity():
    assert return_on_equity(100, 20, -30) is None


# ============================================================
# RETURN ON CAPITAL EMPLOYED
# ============================================================

def test_roce_normal():
    assert return_on_capital_employed(
        200, 100, 400, 500
    ) == 20.0


# ============================================================
# RETURN ON ASSETS
# ============================================================

def test_roa_normal():
    assert return_on_assets(100, 1000) == 10.0


def test_roa_zero_assets():
    assert return_on_assets(100, 0) is None
# ============================================================
# Day 09 - Leverage & Efficiency Ratios
# ============================================================

def test_debt_to_equity_normal():
    assert debt_to_equity(200, 100, 300) == 0.5


def test_debt_to_equity_debt_free():
    assert debt_to_equity(0, 100, 300) == 0


def test_high_leverage_flag():
    assert high_leverage_flag(6, "Energy") is True


def test_financials_high_leverage_suppressed():
    assert high_leverage_flag(6, "Financials") is False


def test_interest_coverage_normal():
    assert interest_coverage_ratio(200, 50, 50) == 5


def test_interest_coverage_debt_free():
    assert interest_coverage_ratio(200, 50, 0) is None


def test_icr_label_debt_free():
    assert icr_label(0) == "Debt Free"


def test_icr_warning():
    assert icr_warning(1.2) is True