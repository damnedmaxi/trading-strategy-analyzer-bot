from datetime import timezone
from typing import Dict, List, Optional

import pandas as pd
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.datafeeds.models import Candle, Symbol

from .config import (
    STRATEGY_INDICATORS,
    STRATEGY_DEFINITIONS,
    STOP_LOSS_ENABLED,
    STOP_LOSS_PERCENT,
    TAKE_PROFIT_ENABLED,
    TAKE_PROFIT_PERCENT,
)
from .indicators import hull_moving_average, simple_moving_average, average_true_range, volume_average
from .models import Strategy
from .serializers import StrategySerializer


class StrategyViewSet(viewsets.ModelViewSet):
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Strategy.objects.all()
        return Strategy.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class HMASMAStrategyRunView(APIView):
    """Evaluate SMA/HMA strategy, returning candles, indicators, and entry markers."""

    BASE_TIMEFRAME = "5m"
    TREND_TIMEFRAME_ONE = "1h"
    TREND_TIMEFRAME_TWO = "4h"
    PERIOD = 200
    VIEW_TIMEFRAMES = {"5m", "30m", "1h", "4h", "1d"}

    def get(self, request, *args, **kwargs):
        symbol_code = request.query_params.get("symbol")
        if not symbol_code:
            raise ValidationError({"symbol": "This query parameter is required."})

        limit_param = request.query_params.get("limit")
        try:
            limit = int(limit_param) if limit_param else None
        except ValueError as exc:
            raise ValidationError({"limit": "Limit must be an integer."}) from exc

        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")
        start_dt = self._parse_datetime(start_param) if start_param else None
        end_dt = self._parse_datetime(end_param) if end_param else None

        try:
            symbol = Symbol.objects.get(code__iexact=symbol_code)
        except Symbol.DoesNotExist as exc:
            raise ValidationError({"symbol": f"Symbol '{symbol_code}' not found."}) from exc

        view_timeframe = request.query_params.get("timeframe", self.BASE_TIMEFRAME)
        if view_timeframe not in self.VIEW_TIMEFRAMES:
            raise ValidationError({"timeframe": f"Unsupported timeframe '{view_timeframe}'."})

        view_df = self._build_dataframe(symbol, view_timeframe, limit, start_dt, end_dt)
        if view_df.empty:
            return Response(
                {
                    "symbol": symbol.code,
                    "timeframe": view_timeframe,
                    "candles": [],
                    "sma200": [],
                    "hma200": {self.TREND_TIMEFRAME_ONE: [], self.TREND_TIMEFRAME_TWO: []},
                    "entries": [],
                    "signal_timeline": [],
                    "latest_signal": None,
                },
                status=status.HTTP_200_OK,
            )

        base_limit = self._calculate_base_limit(view_timeframe, limit)
        base_df = self._build_dataframe(symbol, self.BASE_TIMEFRAME, base_limit, start_dt, end_dt)
        if base_df.empty:
            return Response(
                {
                    "symbol": symbol.code,
                    "timeframe": view_timeframe,
                    "candles": [],
                    "sma200": [],
                    "hma200": {self.TREND_TIMEFRAME_ONE: [], self.TREND_TIMEFRAME_TWO: []},
                    "entries": [],
                    "signal_timeline": [],
                    "latest_signal": None,
                },
                status=status.HTTP_200_OK,
            )

        trend_one_df = self._build_dataframe(symbol, self.TREND_TIMEFRAME_ONE, None, start_dt, end_dt)
        trend_two_df = self._build_dataframe(symbol, self.TREND_TIMEFRAME_TWO, None, start_dt, end_dt)
        trend_three_df = self._build_dataframe(symbol, "1d", None, start_dt, end_dt)

        base_df["sma200"] = simple_moving_average(base_df["close"], self.PERIOD)
        if not trend_one_df.empty:
            trend_one_df["hma200"] = hull_moving_average(trend_one_df["close"], self.PERIOD)
            # Needed for Strategy 4 conditions
            trend_one_df["sma200"] = simple_moving_average(trend_one_df["close"], self.PERIOD)
        if not trend_two_df.empty:
            trend_two_df["hma200"] = hull_moving_average(trend_two_df["close"], self.PERIOD)
        if not trend_three_df.empty:
            # Daily bias filter for Strategy 4
            trend_three_df["hma200"] = hull_moving_average(trend_three_df["close"], self.PERIOD)

        view_df["sma200_view"] = simple_moving_average(view_df["close"], self.PERIOD)

        merged = self._merge_trend_frames(base_df, trend_one_df, trend_two_df)
        # Merge additional indicators required by Strategy 4
        if not trend_one_df.empty and "sma200" in trend_one_df.columns:
            merged = pd.merge_asof(
                merged,
                trend_one_df.sort_values("timestamp")[["timestamp", "sma200"]],
                on="timestamp",
                direction="backward",
                tolerance=pd.Timedelta("6h"),
            ).rename(columns={"sma200": "sma200_1h"})
        else:
            merged["sma200_1h"] = pd.NA

        if not trend_three_df.empty and "hma200" in trend_three_df.columns:
            merged = pd.merge_asof(
                merged,
                trend_three_df.sort_values("timestamp")[["timestamp", "hma200"]],
                on="timestamp",
                direction="backward",
                tolerance=pd.Timedelta("5d"),
            ).rename(columns={"hma200": "hma200_1d"})
        else:
            merged["hma200_1d"] = pd.NA

        # Normalize column names if merge created suffixes
        if "sma200_x" in merged.columns and "sma200" not in merged.columns:
            merged = merged.rename(columns={"sma200_x": "sma200"})
        if "sma200_y" in merged.columns and "sma200_1h" not in merged.columns:
            merged = merged.rename(columns={"sma200_y": "sma200_1h"})

        # Select strategy based on request parameter
        strategy_param = request.query_params.get("strategy", "1")
        if strategy_param == "2":
            evaluations, entries = self._evaluate_entries_strategy2(merged)
        elif strategy_param == "3":
            # Calculate additional indicators for Strategy 3
            merged = self._calculate_strategy3_indicators(merged)
            evaluations, entries = self._evaluate_entries_strategy3(merged)
        elif strategy_param == "4":
            evaluations, entries = self._evaluate_entries_strategy4(merged)
        else:
            evaluations, entries = self._evaluate_entries(merged)

        latest_signal = evaluations[-1] if evaluations else None
        aligned_entries = self._align_entries(entries, view_df, view_timeframe)

        indicator_payload = self._build_indicator_payload(
            symbol=symbol,
            cached_frames={
                self.BASE_TIMEFRAME: base_df,
                view_timeframe: view_df,
                self.TREND_TIMEFRAME_ONE: trend_one_df,
                self.TREND_TIMEFRAME_TWO: trend_two_df,
            },
            view_timeframe=view_timeframe,
            view_limit=limit,
            base_limit=base_limit,
            start_dt=start_dt,
            end_dt=end_dt,
        )

        payload = {
            "symbol": symbol.code,
            "timeframe": view_timeframe,
            "candles": self._serialize_candles(view_df),
            "indicators": indicator_payload,
            "entries": aligned_entries,
            "signal_timeline": evaluations,
            "latest_signal": latest_signal,
        }

        return Response(payload, status=status.HTTP_200_OK)

    @staticmethod
    def _parse_datetime(value: str):
        dt = parse_datetime(value)
        if dt is None:
            raise ValidationError({"datetime": f"Invalid datetime format: {value}"})
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _build_dataframe(symbol: Symbol, timeframe: str, limit: int, start_dt, end_dt):
        qs = Candle.objects.filter(symbol=symbol, timeframe=timeframe)
        if start_dt:
            qs = qs.filter(timestamp__gte=start_dt)
        if end_dt:
            qs = qs.filter(timestamp__lte=end_dt)
        qs = qs.order_by("-timestamp")
        if limit:
            qs = qs[:limit]
        candles = list(qs)
        candles.reverse()
        if not candles:
            return pd.DataFrame()
        frame = pd.DataFrame(
            {
                "timestamp": [c.timestamp for c in candles],
                "open": [float(c.open) for c in candles],
                "high": [float(c.high) for c in candles],
                "low": [float(c.low) for c in candles],
                "close": [float(c.close) for c in candles],
                "volume": [float(c.volume) for c in candles],
            }
        )
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        return frame


 

    def _merge_trend_frames(self, base_df: pd.DataFrame, trend_one_df: pd.DataFrame, trend_two_df: pd.DataFrame) -> pd.DataFrame:
        merged = base_df.sort_values("timestamp").copy()

        if not trend_one_df.empty:
            merged = pd.merge_asof(
                merged,
                trend_one_df.sort_values("timestamp")[["timestamp", "hma200"]],
                on="timestamp",
                direction="backward",
                tolerance=pd.Timedelta("6h"),
            ).rename(columns={"hma200": "hma200_1h"})
        else:
            merged["hma200_1h"] = pd.NA

        if not trend_two_df.empty:
            merged = pd.merge_asof(
                merged,
                trend_two_df.sort_values("timestamp")[["timestamp", "hma200"]],
                on="timestamp",
                direction="backward",
                tolerance=pd.Timedelta("1d"),
            ).rename(columns={"hma200": "hma200_4h"})
        else:
            merged["hma200_4h"] = pd.NA

        return merged

    def _calculate_strategy3_indicators(self, merged: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate additional indicators needed for Strategy 3 (Smart Crossover Hybrid).
        
        Args:
            merged: DataFrame with basic indicators already calculated
            
        Returns:
            DataFrame with additional indicators for Strategy 3
        """
        # ATR(14) for volatility measurement
        merged["atr14"] = average_true_range(
            high=merged["high"],
            low=merged["low"], 
            close=merged["close"],
            period=14
        )
        
        # Volume Average(20) for volume confirmation
        merged["volume_avg20"] = volume_average(
            volume=merged["volume"],
            period=20
        )
        
        # ATR as percentage of price for volatility filter
        merged["atr_percent"] = (merged["atr14"] / merged["close"]) * 100
        
        # Volume ratio for volume confirmation
        merged["volume_ratio"] = merged["volume"] / merged["volume_avg20"]
        
        return merged

    def _evaluate_entries(self, merged: pd.DataFrame):
        """Strategy 1: Multi-timeframe alignment strategy"""
        entries: List[Dict] = []
        evaluations: List[Dict] = []
        # Track actual open positions (not entry conditions)
        position_long_open = False
        position_short_open = False

        for row in merged.itertuples():
            sma = getattr(row, "sma200")
            if pd.isna(sma):
                position_long_open = False
                position_short_open = False
                continue

            open_5m = float(row.open)
            hma_1h_raw = getattr(row, "hma200_1h")
            hma_4h_raw = getattr(row, "hma200_4h")

            hma_1h_value = None if pd.isna(hma_1h_raw) else float(hma_1h_raw)
            hma_4h_value = None if pd.isna(hma_4h_raw) else float(hma_4h_raw)

            price_5m = float(row.close)
            close_below_both = (
                hma_1h_value is not None
                and hma_4h_value is not None
                and position_long_open
                and open_5m < hma_1h_value
                and price_5m < hma_1h_value
                and open_5m < hma_4h_value
                and price_5m < hma_4h_value
            )
            close_above_both = (
                hma_1h_value is not None
                and hma_4h_value is not None
                and position_short_open
                and open_5m > hma_1h_value
                and price_5m > hma_1h_value
                and open_5m > hma_4h_value
                and price_5m > hma_4h_value
            )

            cond_5m_long = price_5m > float(sma)
            cond_5m_short = price_5m < float(sma)
            cond_1h_long = hma_1h_value is not None and price_5m > hma_1h_value
            cond_1h_short = hma_1h_value is not None and price_5m < hma_1h_value
            cond_4h_long = hma_4h_value is not None and price_5m > hma_4h_value
            cond_4h_short = hma_4h_value is not None and price_5m < hma_4h_value

            should_long = cond_5m_long and cond_1h_long and cond_4h_long
            should_short = cond_5m_short and cond_1h_short and cond_4h_short
            
            # Exit when both open and close are on the opposite side of SMA
            exit_long = position_long_open and (row.open < float(sma)) and (price_5m < float(sma))
            exit_short = position_short_open and (row.open > float(sma)) and (price_5m > float(sma))

            timestamp_iso = row.timestamp.isoformat()
            evaluations.append(
                {
                    "time": timestamp_iso,
                    "should_enter": should_long,
                    "should_enter_long": should_long,
                    "should_enter_short": should_short,
                    "should_exit_long": exit_long,
                    "should_exit_short": exit_short,
                    "breakdown": {
                        "5m": {
                            "price": price_5m,
                            "indicator": float(sma),
                            "condition_met": cond_5m_long,
                            "condition_long": cond_5m_long,
                            "condition_short": cond_5m_short,
                        },
                        "1h": {
                            "price": price_5m,
                            "indicator": hma_1h,
                            "condition_met": cond_1h_long,
                            "condition_long": cond_1h_long,
                            "condition_short": cond_1h_short,
                        },
                        "4h": {
                            "price": price_5m,
                            "indicator": hma_4h,
                            "condition_met": cond_4h_long,
                            "condition_long": cond_4h_long,
                            "condition_short": cond_4h_short,
                        },
                    },
                }
            )

            # Close positions first
            if exit_long:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long_exit",
                        "price": price_5m,
                    }
                )
                position_long_open = False
                
            if exit_short:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short_exit",
                        "price": price_5m,
                    }
                )
                position_short_open = False

            # Open new positions only if not already in one
            if should_long and not position_long_open and not position_short_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long",
                        "price": price_5m,
                    }
                )
                position_long_open = True
                
            if should_short and not position_short_open and not position_long_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short",
                        "price": price_5m,
                    }
                )
                position_short_open = True

        return evaluations, entries

    def _evaluate_entries_strategy2(self, merged: pd.DataFrame):
        """Strategy 2: SMA 200 5m crossover strategy with HMA 200 1h/4h"""
        entries: List[Dict] = []
        evaluations: List[Dict] = []
        # Track actual open positions
        position_long_open = False
        position_short_open = False

        # Active stop-loss/take-profit levels
        long_stop_price: Optional[float] = None
        long_take_price: Optional[float] = None
        short_stop_price: Optional[float] = None
        short_take_price: Optional[float] = None

        # Variables to store previous values for crossover detection
        prev_sma = None
        prev_hma_1h = None
        prev_hma_4h = None

        loss_factor = (STOP_LOSS_PERCENT / 100) if STOP_LOSS_ENABLED and STOP_LOSS_PERCENT > 0 else None
        profit_factor = (TAKE_PROFIT_PERCENT / 100) if TAKE_PROFIT_ENABLED and TAKE_PROFIT_PERCENT > 0 else None

        for row in merged.itertuples():
            sma = getattr(row, "sma200")
            if pd.isna(sma):
                position_long_open = False
                position_short_open = False
                long_stop_price = None
                long_take_price = None
                short_stop_price = None
                short_take_price = None
                prev_sma = None
                prev_hma_1h = None
                prev_hma_4h = None
                continue

            sma_value = float(sma)
            hma_1h = getattr(row, "hma200_1h")
            hma_4h = getattr(row, "hma200_4h")

            hma_1h_value = None if pd.isna(hma_1h) else float(hma_1h)
            hma_4h_value = None if pd.isna(hma_4h) else float(hma_4h)
            price_5m = float(row.close)
            open_5m = float(row.open)

            high_5m = float(row.high)
            low_5m = float(row.low)

            candidate_stop_loss_long = None
            candidate_stop_loss_short = None
            candidate_take_profit_long = None
            candidate_take_profit_short = None

            if loss_factor is not None:
                candidate_stop_loss_long = price_5m * (1 - loss_factor)
                candidate_stop_loss_short = price_5m * (1 + loss_factor)

            if profit_factor is not None:
                candidate_take_profit_long = price_5m * (1 + profit_factor)
                candidate_take_profit_short = price_5m * (1 - profit_factor)

            close_below_both = (
                position_long_open
                and hma_1h_value is not None
                and hma_4h_value is not None
                and open_5m < hma_1h_value
                and price_5m < hma_1h_value
                and open_5m < hma_4h_value
                and price_5m < hma_4h_value
            )
            close_above_both = (
                position_short_open
                and hma_1h_value is not None
                and hma_4h_value is not None
                and open_5m > hma_1h_value
                and price_5m > hma_1h_value
                and open_5m > hma_4h_value
                and price_5m > hma_4h_value
            )

            # Detect crossovers
            # Entry LONG: SMA 5m crosses above HMA 4h
            crossover_long = False
            if prev_sma is not None and prev_hma_4h is not None and hma_4h_value is not None:
                crossover_long = prev_sma <= prev_hma_4h and sma_value > hma_4h_value
            
            # Exit LONG conditions:
            # 1) SMA 5m crosses below HMA 1h
            crossover_exit_long_1h = False
            if prev_sma is not None and prev_hma_1h is not None and hma_1h_value is not None:
                crossover_exit_long_1h = prev_sma >= prev_hma_1h and sma_value < hma_1h_value
            
            # 2) SMA 5m crosses below HMA 4h (SHORT entry signal)
            crossover_exit_long_4h = False
            if prev_sma is not None and prev_hma_4h is not None and hma_4h_value is not None:
                crossover_exit_long_4h = prev_sma >= prev_hma_4h and sma_value < hma_4h_value
            
            # Entry SHORT: SMA 5m crosses below HMA 4h
            crossover_short = False
            if prev_sma is not None and prev_hma_4h is not None and hma_4h_value is not None:
                crossover_short = prev_sma >= prev_hma_4h and sma_value < hma_4h_value
            
            # Exit SHORT conditions:
            # 1) SMA 5m crosses above HMA 1h
            crossover_exit_short_1h = False
            if prev_sma is not None and prev_hma_1h is not None and hma_1h_value is not None:
                crossover_exit_short_1h = prev_sma <= prev_hma_1h and sma_value > hma_1h_value
            
            # 2) SMA 5m crosses above HMA 4h (LONG entry signal)
            crossover_exit_short_4h = False
            if prev_sma is not None and prev_hma_4h is not None and hma_4h_value is not None:
                crossover_exit_short_4h = prev_sma <= prev_hma_4h and sma_value > hma_4h_value

            should_long = crossover_long
            should_short = crossover_short

            stop_long_trigger = False
            take_long_trigger = False
            stop_short_trigger = False
            take_short_trigger = False

            if position_long_open:
                if long_stop_price is not None:
                    stop_long_trigger = low_5m <= long_stop_price or open_5m <= long_stop_price
                if long_take_price is not None:
                    take_long_trigger = high_5m >= long_take_price or open_5m >= long_take_price

            if position_short_open:
                if short_stop_price is not None:
                    stop_short_trigger = high_5m >= short_stop_price or open_5m >= short_stop_price
                if short_take_price is not None:
                    take_short_trigger = low_5m <= short_take_price or open_5m <= short_take_price

            exit_long_reason = None
            exit_long_price = price_5m
            if position_long_open:
                if stop_long_trigger:
                    exit_long_reason = "stop_loss"
                    exit_long_price = long_stop_price
                elif take_long_trigger:
                    exit_long_reason = "take_profit"
                    exit_long_price = long_take_price
                elif close_below_both:
                    exit_long_reason = "body_break"
                elif crossover_exit_long_1h or crossover_exit_long_4h:
                    exit_long_reason = "crossover"

            exit_short_reason = None
            exit_short_price = price_5m
            if position_short_open:
                if stop_short_trigger:
                    exit_short_reason = "stop_loss"
                    exit_short_price = short_stop_price
                elif take_short_trigger:
                    exit_short_reason = "take_profit"
                    exit_short_price = short_take_price
                elif close_above_both:
                    exit_short_reason = "body_break"
                elif crossover_exit_short_1h or crossover_exit_short_4h:
                    exit_short_reason = "crossover"

            exit_long = exit_long_reason is not None
            exit_short = exit_short_reason is not None

            timestamp_iso = row.timestamp.isoformat()

            current_long_stop = long_stop_price
            current_long_take = long_take_price
            current_short_stop = short_stop_price
            current_short_take = short_take_price

            evaluations.append(
                {
                    "time": timestamp_iso,
                    "should_enter": should_long,
                    "should_enter_long": should_long,
                    "should_enter_short": should_short,
                    "should_exit_long": exit_long,
                    "should_exit_short": exit_short,
                    "exit_reason_long": exit_long_reason,
                    "exit_reason_short": exit_short_reason,
                    "active_stop_loss_long": current_long_stop,
                    "active_take_profit_long": current_long_take,
                    "active_stop_loss_short": current_short_stop,
                    "active_take_profit_short": current_short_take,
                    "stop_loss_triggered_long": stop_long_trigger,
                    "take_profit_triggered_long": take_long_trigger,
                    "stop_loss_triggered_short": stop_short_trigger,
                    "take_profit_triggered_short": take_short_trigger,
                    "breakdown": {
                        "5m": {
                            "price": price_5m,
                            "indicator": sma_value,
                            "condition_met": should_long,
                            "condition_long": should_long,
                            "condition_short": should_short,
                        },
                        "1h": {
                            "price": price_5m,
                            "indicator": hma_1h_value,
                            "condition_met": False,
                            "condition_long": not crossover_exit_long_1h if position_long_open else False,
                            "condition_short": crossover_exit_short_1h if position_short_open else False,
                            "exit_on_body_break": close_below_both if position_long_open else close_above_both,
                        },
                        "4h": {
                            "price": price_5m,
                            "indicator": hma_4h_value,
                            "condition_met": should_long,
                            "condition_long": crossover_long,
                            "condition_short": crossover_short,
                            "exit_on_body_break": close_below_both if position_long_open else close_above_both,
                        },
                    },
                }
            )

            # Close positions first so a crossover can flip immediately
            if exit_long:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long_exit",
                        "price": exit_long_price,
                        "reason": exit_long_reason,
                    }
                )
                position_long_open = False
                long_stop_price = None
                long_take_price = None
                
            if exit_short:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short_exit",
                        "price": exit_short_price,
                        "reason": exit_short_reason,
                    }
                )
                position_short_open = False
                short_stop_price = None
                short_take_price = None

            # Open new positions only if not already in one
            if should_long and not position_long_open and not position_short_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long",
                        "price": price_5m,
                        "stop_loss": candidate_stop_loss_long,
                        "take_profit": candidate_take_profit_long,
                        "stop_loss_percent": STOP_LOSS_PERCENT if STOP_LOSS_ENABLED else None,
                        "take_profit_percent": TAKE_PROFIT_PERCENT if TAKE_PROFIT_ENABLED else None,
                    }
                )
                position_long_open = True
                long_stop_price = candidate_stop_loss_long
                long_take_price = candidate_take_profit_long
                
            if should_short and not position_short_open and not position_long_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short",
                        "price": price_5m,
                        "stop_loss": candidate_stop_loss_short,
                        "take_profit": candidate_take_profit_short,
                        "stop_loss_percent": STOP_LOSS_PERCENT if STOP_LOSS_ENABLED else None,
                        "take_profit_percent": TAKE_PROFIT_PERCENT if TAKE_PROFIT_ENABLED else None,
                    }
                )
                position_short_open = True
                short_stop_price = candidate_stop_loss_short
                short_take_price = candidate_take_profit_short

            # Update previous values for next iteration
            prev_sma = sma_value
            prev_hma_1h = hma_1h_value
            prev_hma_4h = hma_4h_value

        return evaluations, entries

    @staticmethod
    def _serialize_candles(frame: pd.DataFrame) -> List[Dict]:
        return [
            {
                "time": row.timestamp.isoformat(),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in frame.itertuples()
        ]

    @staticmethod
    def _serialize_indicator(frame: pd.DataFrame, column: str) -> List[Dict]:
        if column not in frame.columns:
            return []
        indicator_series = frame[["timestamp", column]].dropna()
        return [
            {
                "time": row.timestamp.isoformat(),
                "value": float(getattr(row, column)),
            }
            for row in indicator_series.itertuples()
        ]

    def _calculate_base_limit(self, view_timeframe: str, limit: int | None) -> int:
        ratio = self._timeframe_ratio(view_timeframe)
        base = max(self.PERIOD + 50, (limit * ratio + self.PERIOD) if limit else self.PERIOD * ratio * 2)
        # Increased limit to allow for longer backtesting periods
        # 100k 5m candles = ~347 days of data
        return min(base, 100000)

    @staticmethod
    def _timeframe_ratio(view_timeframe: str) -> int:
        mapping = {
            "5m": 1,
            "30m": 6,
            "1h": 12,
            "4h": 48,
            "1d": 288,
        }
        return mapping.get(view_timeframe, 1)

    def _timeframe_delta(self, timeframe: str) -> pd.Timedelta:
        mapping = {
            "5m": pd.Timedelta(minutes=5),
            "30m": pd.Timedelta(minutes=30),
            "1h": pd.Timedelta(hours=1),
            "4h": pd.Timedelta(hours=4),
            "1d": pd.Timedelta(days=1),
        }
        return mapping.get(timeframe, pd.Timedelta(minutes=5))

    def _align_entries(self, entries: List[Dict], view_df: pd.DataFrame, view_timeframe: str) -> List[Dict]:
        if not entries or view_df.empty:
            return []
        if view_timeframe == self.BASE_TIMEFRAME:
            return [
                {
                    "time": entry["timestamp"].isoformat(),
                    "source_time": entry["timestamp"].isoformat(),
                    "direction": entry["direction"],
                    "price": entry.get("price"),
                }
                for entry in entries
            ]

        timestamps = list(view_df["timestamp"])
        if not timestamps:
            return []
        delta = self._timeframe_delta(view_timeframe)
        window_end = timestamps[1:] + [timestamps[-1] + delta]

        aligned = []
        for entry in entries:
            raw_ts = entry["timestamp"]
            entry_ts = pd.Timestamp(raw_ts)
            if entry_ts.tz is None:
                entry_ts = entry_ts.tz_localize("UTC")
            else:
                entry_ts = entry_ts.tz_convert("UTC")
            candle_ts = None
            for start_ts, end_ts in zip(timestamps, window_end):
                if start_ts <= entry_ts < end_ts:
                    candle_ts = start_ts
                    break
            if candle_ts is None:
                if entry_ts >= timestamps[-1]:
                    candle_ts = timestamps[-1]
                else:
                    continue
            aligned.append(
                {
                    "time": candle_ts.isoformat(),
                    "source_time": entry_ts.isoformat(),
                    "direction": entry["direction"],
                    "price": entry.get("price"),
                }
            )
        return aligned

    def _build_indicator_payload(
        self,
        symbol: Symbol,
        cached_frames: Dict[str, pd.DataFrame],
        view_timeframe: str,
        view_limit: Optional[int],
        base_limit: int,
        start_dt,
        end_dt,
    ) -> Dict[str, Dict[str, List[Dict]]]:
        payload: Dict[str, Dict[str, List[Dict]]] = {"sma": {}, "hma": {}}
        frame_cache = dict(cached_frames)

        for indicator_type, timeframe_map in STRATEGY_INDICATORS.items():
            indicator_results: Dict[str, List[Dict]] = {}
            for timeframe, cfg in timeframe_map.items():
                # Backwards-compatible handling: bool => calc+plot, dict => explicit flags
                if isinstance(cfg, bool):
                    calc = cfg
                    plot = cfg
                elif isinstance(cfg, dict):
                    calc = bool(cfg.get("calc", False))
                    plot = bool(cfg.get("plot", calc))
                else:
                    calc = False
                    plot = False

                if not calc:
                    continue

                limit = base_limit if timeframe == self.BASE_TIMEFRAME else view_limit
                df = self._get_dataframe_for_indicator(symbol, timeframe, frame_cache, limit, start_dt, end_dt)
                if df is None or df.empty:
                    # If plotting was requested but no data, surface empty list
                    if plot:
                        indicator_results[timeframe] = []
                    continue

                series = self._compute_indicator_series(df.copy(), indicator_type, timeframe)
                if plot:
                    indicator_results[timeframe] = series
            payload[indicator_type] = indicator_results

        return payload

    def _get_dataframe_for_indicator(
        self,
        symbol: Symbol,
        timeframe: str,
        cache: Dict[str, pd.DataFrame],
        limit: Optional[int],
        start_dt,
        end_dt,
    ) -> pd.DataFrame:
        df = cache.get(timeframe)
        if df is not None and not df.empty:
            return df
        df = self._build_dataframe(symbol, timeframe, limit, start_dt, end_dt)
        cache[timeframe] = df
        return df

    def _compute_indicator_series(self, frame: pd.DataFrame, indicator_type: str, timeframe: str) -> List[Dict]:
        if frame.empty:
            return []
        column_name = f"{indicator_type}200_{timeframe}"
        if indicator_type == "sma":
            frame[column_name] = simple_moving_average(frame["close"], self.PERIOD)
        else:
            frame[column_name] = hull_moving_average(frame["close"], self.PERIOD)
        return self._serialize_indicator(frame, column_name)

    def _evaluate_entries_strategy3(self, merged: pd.DataFrame):
        """Strategy 3: Smart Crossover Hybrid with Risk Management"""
        entries: List[Dict] = []
        evaluations: List[Dict] = []
        
        # Track actual open positions
        position_long_open = False
        position_short_open = False
        
        # Variables to store previous values for crossover detection
        prev_sma = None
        prev_hma_1h = None
        prev_hma_4h = None
        
        # Risk management parameters
        ATR_MULTIPLIER = 2.0
        MAX_ATR_PERCENT = 3.0
        RISK_PER_TRADE = 1.0
        MIN_RR_RATIO = 2.0

        for row in merged.itertuples():
            sma = getattr(row, "sma200")
            if pd.isna(sma):
                position_long_open = False
                position_short_open = False
                prev_sma = None
                prev_hma_1h = None
                prev_hma_4h = None
                continue

            sma_value = float(sma)
            hma_1h = getattr(row, "hma200_1h")
            hma_4h = getattr(row, "hma200_4h")
            atr14 = getattr(row, "atr14")
            atr_percent = getattr(row, "atr_percent")
            volume_ratio = getattr(row, "volume_ratio")

            hma_1h_value = None if pd.isna(hma_1h) else float(hma_1h)
            hma_4h_value = None if pd.isna(hma_4h) else float(hma_4h)
            atr14_value = None if pd.isna(atr14) else float(atr14)
            atr_percent_value = None if pd.isna(atr_percent) else float(atr_percent)
            volume_ratio_value = None if pd.isna(volume_ratio) else float(volume_ratio)

            price_5m = float(row.close)

            # Detect crossovers (base from Strategy 2)
            crossover_long = False
            crossover_short = False
            
            if prev_sma is not None and prev_hma_4h is not None and hma_4h_value is not None:
                crossover_long = prev_sma <= prev_hma_4h and sma_value > hma_4h_value
                crossover_short = prev_sma >= prev_hma_4h and sma_value < hma_4h_value

            # ========== STRATEGY 3 FILTERS ==========
            # Additional filters for higher precision
            
            # Volatility filter: Skip if ATR > 3% of price
            volatility_ok = atr_percent_value is None or atr_percent_value <= MAX_ATR_PERCENT
            
            # Volume filter: Require volume > average
            volume_ok = volume_ratio_value is None or volume_ratio_value > 1.0
            
            # Trend filter: Price must be on correct side of SMA
            trend_long_ok = price_5m > sma_value
            trend_short_ok = price_5m < sma_value
            
            # Multi-timeframe confirmation
            mtf_long_ok = hma_1h_value is not None and hma_4h_value is not None and hma_1h_value > hma_4h_value
            mtf_short_ok = hma_1h_value is not None and hma_4h_value is not None and hma_1h_value < hma_4h_value
            
            # Apply all filters
            should_long = (crossover_long and volatility_ok and volume_ok and 
                          trend_long_ok and mtf_long_ok)
            should_short = (crossover_short and volatility_ok and volume_ok and 
                           trend_short_ok and mtf_short_ok)
            # =========================================

            # Exit conditions (simplified for now)
            exit_long = position_long_open and (row.open < sma_value) and (price_5m < sma_value)
            exit_short = position_short_open and (row.open > sma_value) and (price_5m > sma_value)

            timestamp_iso = row.timestamp.isoformat()
            
            # Calculate stop loss and take profit levels
            stop_loss_long = None
            take_profit_long = None
            stop_loss_short = None
            take_profit_short = None
            
            if atr14_value is not None:
                # Long position risk management
                stop_loss_long = price_5m - (atr14_value * ATR_MULTIPLIER)
                take_profit_long = price_5m + (atr14_value * ATR_MULTIPLIER * MIN_RR_RATIO)
                
                # Short position risk management
                stop_loss_short = price_5m + (atr14_value * ATR_MULTIPLIER)
                take_profit_short = price_5m - (atr14_value * ATR_MULTIPLIER * MIN_RR_RATIO)

            evaluations.append(
                {
                    "time": timestamp_iso,
                    "should_enter": should_long,
                    "should_enter_long": should_long,
                    "should_enter_short": should_short,
                    "should_exit_long": exit_long,
                    "should_exit_short": exit_short,
                    # Strategy 3 specific information
                    "atr14": atr14_value,
                    "atr_percent": atr_percent_value,
                    "volume_ratio": volume_ratio_value,
                    "volatility_ok": volatility_ok,
                    "volume_ok": volume_ok,
                    "crossover_long": crossover_long,
                    "crossover_short": crossover_short,
                    "stop_loss_long": stop_loss_long,
                    "take_profit_long": take_profit_long,
                    "stop_loss_short": stop_loss_short,
                    "take_profit_short": take_profit_short,
                    "breakdown": {
                        "5m": {
                            "price": price_5m,
                            "indicator": sma_value,
                            "condition_met": should_long,
                            "condition_long": should_long,
                            "condition_short": should_short,
                        },
                        "1h": {
                            "price": price_5m,
                            "indicator": hma_1h_value,
                            "condition_met": mtf_long_ok,
                            "condition_long": mtf_long_ok,
                            "condition_short": mtf_short_ok,
                        },
                        "4h": {
                            "price": price_5m,
                            "indicator": hma_4h_value,
                            "condition_met": should_long,
                            "condition_long": should_long,
                            "condition_short": should_short,
                        },
                    },
                }
            )

            # Update previous values for next iteration
            prev_sma = sma_value
            prev_hma_1h = hma_1h_value
            prev_hma_4h = hma_4h_value

            # Open new positions only if not already in one
            if should_long and not position_long_open and not position_short_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long",
                        "price": price_5m,
                        "stop_loss": stop_loss_long,
                        "take_profit": take_profit_long,
                        "atr": atr14_value,
                        "risk_percent": RISK_PER_TRADE,
                    }
                )
                position_long_open = True

            if should_short and not position_short_open and not position_long_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short",
                        "price": price_5m,
                        "stop_loss": stop_loss_short,
                        "take_profit": take_profit_short,
                        "atr": atr14_value,
                        "risk_percent": RISK_PER_TRADE,
                    }
                )
                position_short_open = True

            # Close positions
            if exit_long:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long_exit",
                        "price": price_5m,
                    }
                )
                position_long_open = False

            if exit_short:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short_exit",
                        "price": price_5m,
                    }
                )
                position_short_open = False

        return evaluations, entries

# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# ####################################################################################################################################################################################

    def _evaluate_entries_strategy4(self, merged: pd.DataFrame):
        """Strategy 4: 5m SMA200 vs 1h HMA200 crossover with 1d bias.

        Long bias: price > HMA200 (1d)
          - Entry long: HMA200 (1h) < SMA200 (1h) and SMA200 (5m) crosses above HMA200 (1h)
          - Exit  long: SMA200 (5m) crosses below HMA200 (1h)

        Short bias: price < HMA200 (1d)
          - Entry short: HMA200 (1h) > SMA200 (1h) and SMA200 (5m) crosses below HMA200 (1h)
          - Exit  short: SMA200 (5m) crosses above HMA200 (1h)
        """
        entries: List[Dict] = []
        evaluations: List[Dict] = []

        position_long_open = False
        position_short_open = False

        # Active stop-loss/take-profit levels (global)
        long_stop_price: Optional[float] = None
        long_take_price: Optional[float] = None
        short_stop_price: Optional[float] = None
        short_take_price: Optional[float] = None

        loss_factor = (STOP_LOSS_PERCENT / 100) if STOP_LOSS_ENABLED and STOP_LOSS_PERCENT > 0 else None
        profit_factor = (TAKE_PROFIT_PERCENT / 100) if TAKE_PROFIT_ENABLED and TAKE_PROFIT_PERCENT > 0 else None

        prev_sma_5m = None
        prev_hma_1h = None

        for row in merged.itertuples():
            sma_5m_raw = getattr(row, "sma200", pd.NA)
            if pd.isna(sma_5m_raw):
                # reset state when insufficient data
                position_long_open = False
                position_short_open = False
                long_stop_price = None
                long_take_price = None
                short_stop_price = None
                short_take_price = None
                prev_sma_5m = None
                prev_hma_1h = None
                continue

            price_5m = float(row.close)
            sma_5m = float(sma_5m_raw)

            hma_1h_raw = getattr(row, "hma200_1h", pd.NA)
            sma_1h_raw = getattr(row, "sma200_1h", pd.NA)
            hma_1d_raw = getattr(row, "hma200_1d", pd.NA)

            hma_1h = None if pd.isna(hma_1h_raw) else float(hma_1h_raw)
            sma_1h = None if pd.isna(sma_1h_raw) else float(sma_1h_raw)
            hma_1d = None if pd.isna(hma_1d_raw) else float(hma_1d_raw)

            open_5m = float(row.open)
            high_5m = float(row.high)
            low_5m = float(row.low)

            candidate_stop_loss_long = None
            candidate_stop_loss_short = None
            candidate_take_profit_long = None
            candidate_take_profit_short = None

            if loss_factor is not None:
                candidate_stop_loss_long = price_5m * (1 - loss_factor)
                candidate_stop_loss_short = price_5m * (1 + loss_factor)

            if profit_factor is not None:
                candidate_take_profit_long = price_5m * (1 + profit_factor)
                candidate_take_profit_short = price_5m * (1 - profit_factor)

            # Bias by daily HMA200 (only SMA200 5m vs HMA200 1d)
            bias_long = hma_1d is not None and sma_5m > hma_1d
            bias_short = hma_1d is not None and sma_5m < hma_1d

            # 1h filter: relationship of HMA200 vs SMA200 on 1h
            filter_1h_long = hma_1h is not None and sma_1h is not None and hma_1h < sma_1h
            filter_1h_short = hma_1h is not None and sma_1h is not None and hma_1h > sma_1h

            # Crossovers between SMA200 5m and HMA200 1h
            crossover_up = False
            crossover_down = False
            if prev_sma_5m is not None and prev_hma_1h is not None and hma_1h is not None:
                crossover_up = prev_sma_5m <= prev_hma_1h and sma_5m > hma_1h
                crossover_down = prev_sma_5m >= prev_hma_1h and sma_5m < hma_1h

            should_long = (bias_long and filter_1h_long and crossover_up)
            should_short = (bias_short and filter_1h_short and crossover_down)

            # Risk management triggers
            stop_long_trigger = False
            take_long_trigger = False
            stop_short_trigger = False
            take_short_trigger = False

            if position_long_open:
                if long_stop_price is not None:
                    stop_long_trigger = low_5m <= long_stop_price or open_5m <= long_stop_price
                if long_take_price is not None:
                    take_long_trigger = high_5m >= long_take_price or open_5m >= long_take_price

            if position_short_open:
                if short_stop_price is not None:
                    stop_short_trigger = high_5m >= short_stop_price or open_5m >= short_stop_price
                if short_take_price is not None:
                    take_short_trigger = low_5m <= short_take_price or open_5m <= short_take_price

            exit_long_reason = None
            exit_short_reason = None

            # Strategy exits plus risk exits
            exit_long = position_long_open and (
                crossover_down or stop_long_trigger or take_long_trigger
            )
            exit_short = position_short_open and (
                crossover_up or stop_short_trigger or take_short_trigger
            )

            if position_long_open:
                if stop_long_trigger:
                    exit_long_reason = "stop_loss"
                elif take_long_trigger:
                    exit_long_reason = "take_profit"
                elif crossover_down:
                    exit_long_reason = "crossover"

            if position_short_open:
                if stop_short_trigger:
                    exit_short_reason = "stop_loss"
                elif take_short_trigger:
                    exit_short_reason = "take_profit"
                elif crossover_up:
                    exit_short_reason = "crossover"

            timestamp_iso = row.timestamp.isoformat()
            evaluations.append(
                {
                    "time": timestamp_iso,
                    "should_enter": should_long or should_short,
                    "should_enter_long": should_long,
                    "should_enter_short": should_short,
                    "should_exit_long": exit_long,
                    "should_exit_short": exit_short,
                    # Incluimos estado de gestión de riesgo para depuración/consistencia
                    "exit_reason_long": exit_long_reason,
                    "exit_reason_short": exit_short_reason,
                    "active_stop_loss_long": long_stop_price,
                    "active_take_profit_long": long_take_price,
                    "active_stop_loss_short": short_stop_price,
                    "active_take_profit_short": short_take_price,
                    "stop_loss_triggered_long": stop_long_trigger,
                    "take_profit_triggered_long": take_long_trigger,
                    "stop_loss_triggered_short": stop_short_trigger,
                    "take_profit_triggered_short": take_short_trigger,
                    "breakdown": {
                        # Show primary relationships; UI expects keys 5m/1h/4h
                        "5m": {
                            "price": price_5m,
                            "indicator": sma_5m,
                            "condition_met": should_long or should_short,
                            "condition_long": should_long,
                            "condition_short": should_short,
                        },
                        "1h": {
                            "price": price_5m,
                            "indicator": hma_1h if hma_1h is not None else None,
                            "condition_met": (filter_1h_long or filter_1h_short),
                            "condition_long": filter_1h_long,
                            "condition_short": filter_1h_short,
                        },
                        # Not used for this strategy; kept for UI compatibility
                        "4h": {
                            "price": price_5m,
                            "indicator": None,
                            "condition_met": False,
                            "condition_long": False,
                            "condition_short": False,
                        },
                    },
                }
            )

            # Process exits first
            if exit_long:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long_exit",
                        "price": price_5m,
                    }
                )
                position_long_open = False
                long_stop_price = None
                long_take_price = None

            if exit_short:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short_exit",
                        "price": price_5m,
                    }
                )
                position_short_open = False
                short_stop_price = None
                short_take_price = None

            # Then process entries if flat
            if should_long and not position_long_open and not position_short_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "long",
                        "price": price_5m,
                        "stop_loss": candidate_stop_loss_long,
                        "take_profit": candidate_take_profit_long,
                        "stop_loss_percent": STOP_LOSS_PERCENT if STOP_LOSS_ENABLED else None,
                        "take_profit_percent": TAKE_PROFIT_PERCENT if TAKE_PROFIT_ENABLED else None,
                    }
                )
                position_long_open = True
                long_stop_price = candidate_stop_loss_long
                long_take_price = candidate_take_profit_long

            if should_short and not position_short_open and not position_long_open:
                entries.append(
                    {
                        "timestamp": row.timestamp.to_pydatetime(),
                        "direction": "short",
                        "price": price_5m,
                        "stop_loss": candidate_stop_loss_short,
                        "take_profit": candidate_take_profit_short,
                        "stop_loss_percent": STOP_LOSS_PERCENT if STOP_LOSS_ENABLED else None,
                        "take_profit_percent": TAKE_PROFIT_PERCENT if TAKE_PROFIT_ENABLED else None,
                    }
                )
                position_short_open = True
                short_stop_price = candidate_stop_loss_short
                short_take_price = candidate_take_profit_short

            # update previous values
            prev_sma_5m = sma_5m
            prev_hma_1h = hma_1h if hma_1h is not None else prev_hma_1h

        return evaluations, entries


class StrategyConfigView(APIView):
    """Expose strategy options and indicator plotting preferences to the frontend."""

    def get(self, request, *args, **kwargs):
        strategies = [s for s in STRATEGY_DEFINITIONS if s.get("enabled", False)]

        # Build styles map from STRATEGY_INDICATORS exposing only plot-related metadata
        indicator_styles: Dict[str, Dict[str, Dict]] = {"sma": {}, "hma": {}}
        for indicator_type, timeframe_map in STRATEGY_INDICATORS.items():
            type_map: Dict[str, Dict] = {}
            for timeframe, cfg in timeframe_map.items():
                if isinstance(cfg, bool):
                    if cfg:
                        type_map[timeframe] = {}
                    continue
                if not isinstance(cfg, dict):
                    continue
                if not cfg.get("plot", False):
                    continue
                meta: Dict[str, object] = {}
                if "color" in cfg:
                    meta["color"] = cfg["color"]
                if "width" in cfg:
                    meta["width"] = cfg["width"]
                type_map[timeframe] = meta
            indicator_styles[indicator_type] = type_map

        return Response(
            {
                "strategies": strategies,
                "indicator_styles": indicator_styles,
            },
            status=status.HTTP_200_OK,
        )
