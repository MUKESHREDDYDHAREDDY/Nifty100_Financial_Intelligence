import pandas as pd

from src.etl.loader import normalize_year, normalize_ticker


# ============================================================
# normalize_year() - 20 tests
# ============================================================

def test_year_integer():
    assert normalize_year(2024) == 2024


def test_year_float():
    assert normalize_year(2024.0) == 2024


def test_year_string():
    assert normalize_year("2024") == 2024


def test_year_decimal_string():
    assert normalize_year("2024.0") == 2024


def test_year_with_decimal():
    assert normalize_year("2024.5") == 2024


def test_year_2023():
    assert normalize_year(2023) == 2023


def test_year_2000():
    assert normalize_year(2000) == 2000


def test_year_1999():
    assert normalize_year("1999") == 1999


def test_year_zero():
    assert normalize_year(0) == 0


def test_year_negative():
    assert normalize_year(-2024) == -2024


def test_year_none():
    assert normalize_year(None) is None


def test_year_nan():
    assert normalize_year(float("nan")) is None


def test_year_pandas_nan():
    assert normalize_year(pd.NaT) is None


def test_year_invalid_text():
    assert normalize_year("abc") is None


def test_year_empty_string():
    assert normalize_year("") is None


def test_year_spaces():
    assert normalize_year("   ") is None


def test_year_special_text():
    assert normalize_year("2024abc") is None


def test_year_boolean_true():
    assert normalize_year(True) == 1


def test_year_boolean_false():
    assert normalize_year(False) == 0


# ============================================================
# normalize_ticker() - 15 tests
# ============================================================

def test_ticker_uppercase():
    assert normalize_ticker("reliance") == "RELIANCE"


def test_ticker_already_uppercase():
    assert normalize_ticker("RELIANCE") == "RELIANCE"


def test_ticker_mixed_case():
    assert normalize_ticker("ReLiAnCe") == "RELIANCE"


def test_ticker_leading_spaces():
    assert normalize_ticker(" reliance") == "RELIANCE"


def test_ticker_trailing_spaces():
    assert normalize_ticker("reliance ") == "RELIANCE"


def test_ticker_both_spaces():
    assert normalize_ticker("  reliance  ") == "RELIANCE"


def test_ticker_tcs():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_infotech():
    assert normalize_ticker("infy") == "INFY"


def test_ticker_with_dot():
    assert normalize_ticker("M&M") == "M&M"


def test_ticker_with_numbers():
    assert normalize_ticker("abc123") == "ABC123"


def test_ticker_none():
    assert normalize_ticker(None) is None


def test_ticker_pandas_na():
    assert normalize_ticker(float("nan")) is None


def test_ticker_pandas_nan():
    assert normalize_ticker(float("nan")) is None


def test_ticker_numeric():
    assert normalize_ticker(500) == "500"


def test_ticker_decimal():
    assert normalize_ticker(500.0) == "500.0"

 
def test_ticker_lowercase():
    assert normalize_ticker(" reliance ") == "RELIANCE" 