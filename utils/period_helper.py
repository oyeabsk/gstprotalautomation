from typing import List, Tuple, Dict
from config.settings import MONTH_NAMES, QUARTERS

def get_quarter_for_month(month: str) -> str:
    """Returns the quarter code ('Q1', 'Q2', 'Q3', 'Q4') for a given month."""
    clean_month = month.strip().capitalize()
    for q_code, months in QUARTERS.items():
        if clean_month in [m.capitalize() for m in months]:
            return q_code
    raise ValueError(f"Invalid month name: {month}")

def get_all_periods_for_fy(fy: str) -> List[Dict[str, str]]:
    """Returns a list of all 12 periods for a financial year in chronological order."""
    periods = []
    for month in MONTH_NAMES:
        periods.append({
            "fy": fy,
            "quarter": get_quarter_for_month(month),
            "month": month
        })
    return periods

def get_period_range(fy: str, start_month: str, end_month: str) -> List[Dict[str, str]]:
    """Returns a list of periods between start_month and end_month (inclusive) for an FY."""
    clean_start = start_month.strip().capitalize()
    clean_end = end_month.strip().capitalize()

    if clean_start not in MONTH_NAMES:
        raise ValueError(f"Invalid start month: {start_month}")
    if clean_end not in MONTH_NAMES:
        raise ValueError(f"Invalid end month: {end_month}")

    start_idx = MONTH_NAMES.index(clean_start)
    end_idx = MONTH_NAMES.index(clean_end)

    if start_idx > end_idx:
        raise ValueError(f"Start month '{start_month}' occurs after end month '{end_month}' in the financial year.")

    selected_months = MONTH_NAMES[start_idx : end_idx + 1]
    return [
        {
            "fy": fy,
            "quarter": get_quarter_for_month(m),
            "month": m
        }
        for m in selected_months
    ]

def get_single_period(fy: str, month: str) -> Dict[str, str]:
    """Returns a single period dict for the given FY and month."""
    clean_month = month.strip().capitalize()
    if clean_month not in MONTH_NAMES:
        raise ValueError(f"Invalid month: {month}")
    return {
        "fy": fy,
        "quarter": get_quarter_for_month(clean_month),
        "month": clean_month
    }

def get_month_sort_prefix(month: str) -> str:
    """
    Returns a 2-digit index prefix with month name (e.g. '01_April', '02_May', ..., '12_March')
    so that downloaded files sort chronologically in ascending order within Windows Explorer.
    """
    clean_month = month.strip().capitalize()
    if clean_month in MONTH_NAMES:
        idx = MONTH_NAMES.index(clean_month) + 1
        return f"{idx:02d}_{clean_month}"
    return month

