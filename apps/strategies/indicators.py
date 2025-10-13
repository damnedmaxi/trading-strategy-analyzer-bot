"""Indicator helpers for strategy modules."""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd


def simple_moving_average(series: pd.Series, period: int) -> pd.Series:
    """Standard SMA with min_periods equal to the window size."""
    validate_series(series, period)
    return series.rolling(window=period, min_periods=period).mean()


def weighted_moving_average(series: pd.Series, period: int) -> pd.Series:
    """Computes a WMA using linear weights (1..period)."""
    validate_series(series, period)
    weights = np.arange(1, period + 1, dtype=float)
    weight_sum = weights.sum()

    def wma_calc(values: np.ndarray) -> float:
        return float(np.dot(values, weights) / weight_sum)

    return series.rolling(window=period, min_periods=period).apply(wma_calc, raw=True)


def hull_moving_average(series: pd.Series, period: int) -> pd.Series:
    """
    Hull Moving Average (HMA):
    HMA(period) = WMA(2 * WMA(series, period / 2) - WMA(series, period), sqrt(period)).
    """
    validate_series(series, period)

    half_period = max(1, period // 2)
    sqrt_period = max(1, int(math.sqrt(period)))

    wma_half = weighted_moving_average(series, half_period)
    wma_full = weighted_moving_average(series, period)

    hull_input = 2 * wma_half - wma_full
    return weighted_moving_average(hull_input, sqrt_period)


def validate_series(series: pd.Series, period: Optional[int]) -> None:
    if not isinstance(series, pd.Series):
        raise TypeError("Indicator functions require a pandas Series input.")
    if period is None or period <= 0:
        raise ValueError("Period must be a positive integer.")
