from src.analytics.cagr import (
    calculate_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)


def test_normal_cagr():
    value, flag = calculate_cagr(100, 121, 2)

    assert round(value, 2) == 10.00
    assert flag is None


def test_positive_to_negative():
    value, flag = calculate_cagr(100, -20, 5)

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_negative_to_positive():
    value, flag = calculate_cagr(-100, 200, 5)

    assert value is None
    assert flag == "TURNAROUND"


def test_both_negative():
    value, flag = calculate_cagr(-100, -200, 5)

    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert flag == "ZERO_BASE"


def test_insufficient_data():
    value, flag = calculate_cagr(None, 100, 5)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_invalid_years():
    value, flag = calculate_cagr(100, 200, 0)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_revenue_cagr():
    value, flag = revenue_cagr(100, 133.1, 3)

    assert round(value, 2) == 10.00
    assert flag is None


def test_pat_cagr():
    value, flag = pat_cagr(100, 121, 2)

    assert round(value, 2) == 10.00
    assert flag is None


def test_eps_cagr():
    value, flag = eps_cagr(50, 60.5, 2)

    assert round(value, 2) == 10.00
    assert flag is None