"""
Simple API client for Bam's stock data service.

Responsibilities:
- Perform HTTP requests to fetch price data.
- Return a normalized dictionary keyed by ticker symbol.
"""

from __future__ import annotations

from typing import Dict, List

import requests

import config


def fetch_prices(symbols: List[str], from_date: str, to_date: str) -> Dict[str, List[dict]]:
    """Fetch daily closing prices for symbols within a date range.

    Calls GET `/v1/prices` on the configured stock API.

    Args:
        symbols: List of ticker symbols (e.g., ["AAPL", "MSFT"]).
        from_date: Start date inclusive in YYYY-MM-DD.
        to_date: End date inclusive in YYYY-MM-DD.

    Returns:
        Mapping from symbol to a list of objects {"date": str, "close": float}.
        Returns an empty dict on request errors. Symbols with no data return an
        empty list in the mapping.
    """

    # Build URL and query
    url = f"{config.STOCK_API_BASE.rstrip('/')}/v1/prices"
    params = {
        "symbols": ",".join(symbols),
        "from": from_date,
        "to": to_date,
    }

    headers: Dict[str, str] = {}
    if config.API_KEY:
        headers["Authorization"] = f"Bearer {config.API_KEY}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=config.TIMEOUT)
        if response.status_code != 200:
            print(f"API returned {response.status_code}: symbols={symbols}, from={from_date}, to={to_date}")
            return {}

        data = response.json()

        result: Dict[str, List[dict]] = {}

        if isinstance(data, dict):
            # Shape: {"AAPL": [{...}, ...], "MSFT": [...], ...}
            for ticker, prices in data.items():
                if prices:
                    result[ticker] = [{"date": p["date"], "close": p["close"]} for p in prices]
                else:
                    result[ticker] = []
        elif isinstance(data, list):
            # Shape: [{"symbol": "AAPL", "date": "YYYY-MM-DD", "close": 123.4, ...}, ...]
            from collections import defaultdict

            tmp = defaultdict(list)
            for row in data:
                sym = row.get("symbol") or row.get("ticker") or row.get("Symbol")
                d = row.get("date") or row.get("Date")
                c = row.get("close") or row.get("Close")
                if not sym or not d or c is None:
                    continue
                tmp[sym].append({"date": d, "close": c})

            # Sort by date ascending for consistency
            result = {k: sorted(v, key=lambda x: x["date"]) for k, v in tmp.items()}
        else:
            print(
                f"Invalid API response format: type={type(data).__name__}, symbols={symbols}, from={from_date}, to={to_date}"
            )
            return {}

        return result

    except requests.Timeout:
        print(f"API timeout: symbols={symbols}, from={from_date}, to={to_date}")
        return {}
    except requests.RequestException as e:
        print(f"API request failed: {e}, symbols={symbols}, from={from_date}, to={to_date}")
        return {}
    except Exception as e:  # pragma: no cover - defensive
        print(f"Unexpected error: {e}, symbols={symbols}, from={from_date}, to={to_date}")
        return {}
