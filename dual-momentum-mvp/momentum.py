"""
Momentum calculation logic.

Responsibilities:
- Compute date ranges and anchors for month/week/day units.
- Fetch price data via the API client.
- Compute simple returns using common anchor dates across symbols.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta

import api_client


def calculate(
    tickers: List[str], unit: str, n: int, as_of_period: str
) -> Tuple[List[Optional[float]], Dict[str, str]]:
    """Calculate momentum values for the given tickers.

    Args:
        tickers: List of ticker symbols.
        unit: One of "month", "week", or "day".
        n: Lookback length in units.
        as_of_period: Anchor period string. Format depends on unit:
            - month: YYYY-MM
            - week/day: YYYY-MM-DD

    Returns:
        A tuple of (results, anchors):
            - results: List of momentums (float) or None per ticker.
            - anchors: {"current": "YYYY-MM-DD", "past": "YYYY-MM-DD"} or "N/A" when unavailable.
    """

    # Step 1: Determine minimal fetch window
    from_date, to_date = calculate_date_range(unit, n, as_of_period)

    # Step 2: Fetch prices
    price_data = api_client.fetch_prices(tickers, from_date, to_date)

    # Step 3: Find common anchors
    current_anchor, past_anchor = find_common_anchors(price_data, unit, n, as_of_period)

    if not current_anchor or not past_anchor:
        return [None] * len(tickers), {"current": "N/A", "past": "N/A"}

    # Step 4: Compute momentum per ticker
    results: List[Optional[float]] = []
    for ticker in tickers:
        if ticker not in price_data or not price_data[ticker]:
            results.append(None)
            continue

        current_price = find_price_on_date(price_data[ticker], current_anchor)
        past_price = find_price_on_date(price_data[ticker], past_anchor)

        if current_price is not None and past_price is not None and past_price != 0:
            momentum_value = (current_price / past_price) - 1
            results.append(momentum_value)
        else:
            results.append(None)

    return results, {"current": current_anchor, "past": past_anchor}


def calculate_date_range(unit: str, n: int, as_of_period: str) -> Tuple[str, str]:
    """Compute a minimal data fetch window for the given unit and period.

    For a balance between simplicity and robustness, we fetch a bit more data
    than the strict minimum to handle gaps and non-trading days.

    Args:
        unit: One of "month", "week", or "day".
        n: Lookback length in units.
        as_of_period: Anchor period string (YYYY-MM for month, YYYY-MM-DD otherwise).

    Returns:
        Tuple of (from_date, to_date) in YYYY-MM-DD.
    """

    if unit == "month":
        # as_of_period is YYYY-MM; anchor uses the previous month's last trading day.
        year, month = map(int, as_of_period.split("-"))
        # Last day of the previous month relative to as_of month
        to_dt = datetime(year, month, 1) + relativedelta(months=1) - timedelta(days=1)
        from_dt = to_dt - relativedelta(months=n + 1)
    else:
        # as_of_period is YYYY-MM-DD
        to_dt = datetime.strptime(as_of_period, "%Y-%m-%d")

        if unit == "week":
            # Round as_of to the Saturday of that week
            to_dt = round_to_saturday(to_dt)
            from_dt = to_dt - timedelta(weeks=n + 1)
        else:  # day
            # Fetch a generous buffer to cover n trading days
            from_dt = to_dt - timedelta(days=(n + 20) * 2)

    return from_dt.strftime("%Y-%m-%d"), to_dt.strftime("%Y-%m-%d")


def round_to_saturday(date: datetime) -> datetime:
    """Round the given date to the Saturday of its week.

    Saturday is considered the end of the week. If the date is already Saturday,
    it returns the same day. If it's Sunday, it rounds to the next Saturday.

    Args:
        date: Any date.

    Returns:
        The Saturday date in the same week or the next Saturday for Sunday.
    """

    days_until_saturday = (5 - date.weekday()) % 7
    if days_until_saturday == 0 and date.weekday() != 5:
        # For Sunday (6 with Python's weekday), push to next Saturday
        days_until_saturday = 7
    return date + timedelta(days=days_until_saturday)


def find_common_anchors(
    price_data: Dict[str, List[Dict]], unit: str, n: int, as_of_period: str
) -> Tuple[Optional[str], Optional[str]]:
    """Find current and past anchor dates present across all symbols.

    Args:
        price_data: Mapping of ticker -> list of {"date": "YYYY-MM-DD", "close": float}.
        unit: One of "month", "week", or "day".
        n: Lookback length in units.
        as_of_period: Anchor period string.

    Returns:
        Tuple of (current_anchor, past_anchor) strings or (None, None) if unavailable.
    """

    if not price_data:
        return None, None

    # Build per-ticker date sets
    date_sets: List[set] = []
    for prices in price_data.values():
        if prices:
            date_sets.append({p["date"] for p in prices})

    if not date_sets:
        return None, None

    common_dates = sorted(set.intersection(*date_sets))
    if not common_dates:
        return None, None

    current_anchor: Optional[str] = None

    if unit == "month":
        # Use the last trading day of the month prior to as_of
        year, month = map(int, as_of_period.split("-"))
        prev_month_end = datetime(year, month, 1) - timedelta(days=1)
        target_prefix = prev_month_end.strftime("%Y-%m")

        for d in reversed(common_dates):
            if d.startswith(target_prefix):
                current_anchor = d
                break

    elif unit == "week":
        base = datetime.strptime(as_of_period, "%Y-%m-%d")
        saturday = round_to_saturday(base)
        week_start = saturday - timedelta(days=6)  # Sunday
        week_end = saturday

        for d in reversed(common_dates):
            d_obj = datetime.strptime(d, "%Y-%m-%d")
            if week_start <= d_obj <= week_end:
                current_anchor = d
                break

    else:  # day
        base = as_of_period  # YYYY-MM-DD string; lexicographic order works
        for d in reversed(common_dates):
            if d <= base:
                current_anchor = d
                break

    if not current_anchor:
        return None, None

    # Past anchor determination
    current_idx = common_dates.index(current_anchor)

    past_anchor: Optional[str]
    if unit == "month":
        current_dt = datetime.strptime(current_anchor, "%Y-%m-%d")
        target_dt = current_dt - relativedelta(months=n)
        target_prefix = target_dt.strftime("%Y-%m")

        past_anchor = None
        for d in reversed(common_dates[:current_idx]):
            if d.startswith(target_prefix):
                past_anchor = d
                break

    elif unit == "week":
        current_dt = datetime.strptime(current_anchor, "%Y-%m-%d")
        target_saturday = current_dt - timedelta(weeks=n)
        target_friday = target_saturday - timedelta(days=1)

        past_anchor = None
        min_diff = float("inf")
        for d in common_dates[:current_idx]:
            d_obj = datetime.strptime(d, "%Y-%m-%d")
            diff = abs((d_obj - target_friday).days)
            if diff < min_diff and diff <= 7:
                min_diff = diff
                past_anchor = d

    else:  # day
        if current_idx >= n:
            past_anchor = common_dates[current_idx - n]
        else:
            past_anchor = None

    return current_anchor, past_anchor


def find_price_on_date(prices: List[Dict], target_date: str) -> Optional[float]:
    """Return the closing price on the target date if present.

    Args:
        prices: List of price dicts with keys "date" and "close".
        target_date: Date string in YYYY-MM-DD format.

    Returns:
        Close price as float, or None if no entry for the date exists.
    """

    for p in prices:
        if p["date"] == target_date:
            return p["close"]
    return None

