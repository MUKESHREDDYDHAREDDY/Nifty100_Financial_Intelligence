import pandas as pd


def normalize_year(value):
    """Normalize year values into integer year format."""

    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        try:
            return int(float(value))
        except (ValueError, TypeError, OverflowError):
            return None

    value = str(value).strip()

    if not value:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError, OverflowError):
        pass

    try:
        date_value = pd.to_datetime(value, errors="coerce")

        if pd.isna(date_value):
            return None

        return int(date_value.year)

    except (ValueError, TypeError, OverflowError):
        return None


def normalize_ticker(value):
    """Normalize stock ticker values."""

    if pd.isna(value):
        return None

    return str(value).strip().upper()