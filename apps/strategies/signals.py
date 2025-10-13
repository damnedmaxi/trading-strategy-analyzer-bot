"""Signal evaluation helpers for the strategy layer."""

from __future__ import annotations

from dataclasses import dataclass
from operator import gt, lt
from typing import Callable, Dict, Mapping, Optional

import pandas as pd

from .indicators import hull_moving_average, simple_moving_average


DEFAULT_PERIOD = 200


@dataclass(frozen=True)
class SignalBreakdown:
    timeframe: str
    price: float
    indicator_value: float
    condition_met: bool
    indicator_name: str
    comparator: str


@dataclass(frozen=True)
class SignalResult:
    should_enter: bool
    breakdown: Mapping[str, SignalBreakdown]
    direction: Optional[str] = None


def evaluate_long_signal(
    closes_by_timeframe: Dict[str, pd.Series],
    sma_period: int = DEFAULT_PERIOD,
    hma_period: int = DEFAULT_PERIOD,
) -> SignalResult:
    """
    Evaluate whether the long-entry conditions are met.

    Required timeframes: 5m (SMA trigger), 1h (HMA trend), 4h (HMA trend).
    """

    return _evaluate_signal(
        closes_by_timeframe=closes_by_timeframe,
        comparator=gt,
        comparator_label=">",
        direction="long",
        sma_period=sma_period,
        hma_period=hma_period,
    )


def evaluate_short_signal(
    closes_by_timeframe: Dict[str, pd.Series],
    sma_period: int = DEFAULT_PERIOD,
    hma_period: int = DEFAULT_PERIOD,
) -> SignalResult:
    """
    Evaluate whether the short-entry conditions are met.

    Rules are the inverse of the long signal (price below indicators).
    """

    return _evaluate_signal(
        closes_by_timeframe=closes_by_timeframe,
        comparator=lt,
        comparator_label="<",
        direction="short",
        sma_period=sma_period,
        hma_period=hma_period,
    )


def _evaluate_signal(
    closes_by_timeframe: Dict[str, pd.Series],
    comparator: Callable[[float, float], bool],
    comparator_label: str,
    direction: str,
    sma_period: int,
    hma_period: int,
) -> SignalResult:
    required_keys = {"5m", "1h", "4h"}
    missing = required_keys - closes_by_timeframe.keys()
    if missing:
        raise KeyError(f"Missing timeframes for evaluation: {', '.join(sorted(missing))}")

    hma_1h = hull_moving_average(closes_by_timeframe["1h"], hma_period).iloc[-1]
    hma_4h = hull_moving_average(closes_by_timeframe["4h"], hma_period).iloc[-1]
    sma_5m = simple_moving_average(closes_by_timeframe["5m"], sma_period).iloc[-1]

    price_map = {
        "1h": closes_by_timeframe["1h"].iloc[-1],
        "4h": closes_by_timeframe["4h"].iloc[-1],
        "5m": closes_by_timeframe["5m"].iloc[-1],
    }

    indicator_map = {
        "1h": ("HMA", hma_1h),
        "4h": ("HMA", hma_4h),
        "5m": ("SMA", sma_5m),
    }

    breakdown = {}
    for timeframe, (indicator_name, indicator_value) in indicator_map.items():
        price_value = price_map[timeframe]
        breakdown[timeframe] = SignalBreakdown(
            timeframe=timeframe,
            price=float(price_value),
            indicator_value=float(indicator_value),
            condition_met=comparator(price_value, indicator_value),
            indicator_name=f"{indicator_name}{hma_period if indicator_name == 'HMA' else sma_period}",
            comparator=comparator_label,
        )

    should_enter = all(item.condition_met for item in breakdown.values())
    direction_value = direction if should_enter else None

    return SignalResult(
        should_enter=should_enter,
        breakdown=breakdown,
        direction=direction_value,
    )


def latest_signal_direction(result: SignalResult) -> Optional[str]:
    """Return the direction string if a trade should trigger."""

    return result.direction
