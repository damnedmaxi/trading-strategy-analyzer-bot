"""Divergence detection algorithms for price vs indicators."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from django.utils import timezone

from apps.datafeeds.models import Candle, Divergence, Symbol
from apps.strategies.indicators import macd, rsi


class DivergenceDetector:
    """Detects divergences between price and indicators."""
    
    def __init__(self, lookback_periods: int = 50):
        """
        Initialize the divergence detector.
        
        Args:
            lookback_periods: Number of periods to look back for divergence detection
        """
        self.lookback_periods = lookback_periods
    
    def detect_all_divergences(self, symbol: Symbol, timeframe: str) -> List[Divergence]:
        """
        Detect all types of divergences for a symbol and timeframe.
        
        Args:
            symbol: Symbol to analyze
            timeframe: Timeframe to analyze (5m, 1h, 4h)
            
        Returns:
            List of detected divergences
        """
        # Get candle data
        candles = self._get_candle_data(symbol, timeframe)
        if len(candles) < self.lookback_periods:
            return []
        
        divergences = []
        
        # Detect MACD divergences
        macd_divergences = self._detect_macd_divergences(candles, symbol, timeframe)
        divergences.extend(macd_divergences)
        
        # Detect RSI divergences
        rsi_divergences = self._detect_rsi_divergences(candles, symbol, timeframe)
        divergences.extend(rsi_divergences)
        
        return divergences
    
    def _get_candle_data(self, symbol: Symbol, timeframe: str) -> pd.DataFrame:
        """Get candle data for analysis."""
        candles = Candle.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('timestamp')
        
        if not candles.exists():
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': float(candle.open),
                'high': float(candle.high),
                'low': float(candle.low),
                'close': float(candle.close),
                'volume': float(candle.volume),
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _detect_macd_divergences(self, df: pd.DataFrame, symbol: Symbol, timeframe: str) -> List[Divergence]:
        """Detect MACD divergences."""
        if len(df) < 50:  # Need enough data for MACD
            return []
        
        # Calculate MACD
        macd_line, signal_line, histogram = macd(df['close'])
        
        # Find local highs and lows in price and MACD
        price_highs = self._find_local_extremes(df['high'], 'high')
        price_lows = self._find_local_extremes(df['low'], 'low')
        macd_highs = self._find_local_extremes(macd_line, 'high')
        macd_lows = self._find_local_extremes(macd_line, 'low')
        
        divergences = []
        
        # Detect bearish divergences (price higher highs, MACD lower highs)
        for i in range(1, len(price_highs)):
            current_high = price_highs[i]
            previous_high = price_highs[i-1]
            
            # Find corresponding MACD highs
            current_macd_high = self._find_corresponding_extreme(
                current_high, macd_highs, df.index
            )
            previous_macd_high = self._find_corresponding_extreme(
                previous_high, macd_highs, df.index
            )
            
            if (current_macd_high and previous_macd_high and
                current_high['value'] > previous_high['value'] and
                current_macd_high['value'] < previous_macd_high['value']):
                
                divergence = Divergence(
                    symbol=symbol,
                    timeframe=timeframe,
                    divergence_type=Divergence.DivergenceType.MACD_BEARISH,
                    start_timestamp=previous_high['timestamp'],
                    start_price=previous_high['value'],
                    start_indicator_value=previous_macd_high['value'],
                    end_timestamp=current_high['timestamp'],
                    end_price=current_high['value'],
                    end_indicator_value=current_macd_high['value'],
                )
                divergences.append(divergence)
        
        # Detect bullish divergences (price lower lows, MACD higher lows)
        for i in range(1, len(price_lows)):
            current_low = price_lows[i]
            previous_low = price_lows[i-1]
            
            # Find corresponding MACD lows
            current_macd_low = self._find_corresponding_extreme(
                current_low, macd_lows, df.index
            )
            previous_macd_low = self._find_corresponding_extreme(
                previous_low, macd_lows, df.index
            )
            
            if (current_macd_low and previous_macd_low and
                current_low['value'] < previous_low['value'] and
                current_macd_low['value'] > previous_macd_low['value']):
                
                divergence = Divergence(
                    symbol=symbol,
                    timeframe=timeframe,
                    divergence_type=Divergence.DivergenceType.MACD_BULLISH,
                    start_timestamp=previous_low['timestamp'],
                    start_price=previous_low['value'],
                    start_indicator_value=previous_macd_low['value'],
                    end_timestamp=current_low['timestamp'],
                    end_price=current_low['value'],
                    end_indicator_value=current_macd_low['value'],
                )
                divergences.append(divergence)
        
        return divergences
    
    def _detect_rsi_divergences(self, df: pd.DataFrame, symbol: Symbol, timeframe: str) -> List[Divergence]:
        """Detect RSI divergences."""
        if len(df) < 30:  # Need enough data for RSI
            return []
        
        # Calculate RSI
        rsi_values = rsi(df['close'])
        
        # Find local highs and lows in price and RSI
        price_highs = self._find_local_extremes(df['high'], 'high')
        price_lows = self._find_local_extremes(df['low'], 'low')
        rsi_highs = self._find_local_extremes(rsi_values, 'high')
        rsi_lows = self._find_local_extremes(rsi_values, 'low')
        
        divergences = []
        
        # Detect bearish divergences (price higher highs, RSI lower highs)
        for i in range(1, len(price_highs)):
            current_high = price_highs[i]
            previous_high = price_highs[i-1]
            
            # Find corresponding RSI highs
            current_rsi_high = self._find_corresponding_extreme(
                current_high, rsi_highs, df.index
            )
            previous_rsi_high = self._find_corresponding_extreme(
                previous_high, rsi_highs, df.index
            )
            
            if (current_rsi_high and previous_rsi_high and
                current_high['value'] > previous_high['value'] and
                current_rsi_high['value'] < previous_rsi_high['value']):
                
                divergence = Divergence(
                    symbol=symbol,
                    timeframe=timeframe,
                    divergence_type=Divergence.DivergenceType.RSI_BEARISH,
                    start_timestamp=previous_high['timestamp'],
                    start_price=previous_high['value'],
                    start_indicator_value=previous_rsi_high['value'],
                    end_timestamp=current_high['timestamp'],
                    end_price=current_high['value'],
                    end_indicator_value=current_rsi_high['value'],
                )
                divergences.append(divergence)
        
        # Detect bullish divergences (price lower lows, RSI higher lows)
        for i in range(1, len(price_lows)):
            current_low = price_lows[i]
            previous_low = price_lows[i-1]
            
            # Find corresponding RSI lows
            current_rsi_low = self._find_corresponding_extreme(
                current_low, rsi_lows, df.index
            )
            previous_rsi_low = self._find_corresponding_extreme(
                previous_low, rsi_lows, df.index
            )
            
            if (current_rsi_low and previous_rsi_low and
                current_low['value'] < previous_low['value'] and
                current_rsi_low['value'] > previous_rsi_low['value']):
                
                divergence = Divergence(
                    symbol=symbol,
                    timeframe=timeframe,
                    divergence_type=Divergence.DivergenceType.RSI_BULLISH,
                    start_timestamp=previous_low['timestamp'],
                    start_price=previous_low['value'],
                    start_indicator_value=previous_rsi_low['value'],
                    end_timestamp=current_low['timestamp'],
                    end_price=current_low['value'],
                    end_indicator_value=current_rsi_low['value'],
                )
                divergences.append(divergence)
        
        return divergences
    
    def _find_local_extremes(self, series: pd.Series, extreme_type: str, window: int = 5) -> List[dict]:
        """
        Find local highs or lows in a series.
        
        Args:
            series: Price or indicator series
            extreme_type: 'high' or 'low'
            window: Window size for local extreme detection
            
        Returns:
            List of extreme points with timestamp and value
        """
        extremes = []
        
        for i in range(window, len(series) - window):
            current_value = series.iloc[i]
            current_timestamp = series.index[i]
            
            # Get window values
            window_start = i - window
            window_end = i + window + 1
            window_values = series.iloc[window_start:window_end]
            
            if extreme_type == 'high':
                # Check if current point is the highest in the window
                if current_value == window_values.max():
                    extremes.append({
                        'timestamp': current_timestamp,
                        'value': current_value,
                        'index': i
                    })
            else:  # low
                # Check if current point is the lowest in the window
                if current_value == window_values.min():
                    extremes.append({
                        'timestamp': current_timestamp,
                        'value': current_value,
                        'index': i
                    })
        
        return extremes
    
    def _find_corresponding_extreme(self, price_extreme: dict, indicator_extremes: List[dict], 
                                  timestamps: pd.DatetimeIndex) -> Optional[dict]:
        """
        Find the corresponding indicator extreme for a price extreme.
        
        Args:
            price_extreme: Price extreme point
            indicator_extremes: List of indicator extremes
            timestamps: DataFrame timestamps
            
        Returns:
            Corresponding indicator extreme or None
        """
        if not indicator_extremes:
            return None
        
        # Find the closest indicator extreme in time
        price_timestamp = price_extreme['timestamp']
        closest_extreme = None
        min_time_diff = float('inf')
        
        for extreme in indicator_extremes:
            time_diff = abs((extreme['timestamp'] - price_timestamp).total_seconds())
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_extreme = extreme
        
        # Only return if within reasonable time window (e.g., 10 periods)
        if min_time_diff < 10 * 3600:  # 10 hours max difference
            return closest_extreme
        
        return None


