from datetime import timezone
from typing import Dict, List, Optional

import pandas as pd
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.datafeeds.models import Candle, Symbol

from .indicators import hull_moving_average, simple_moving_average
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

        base_df["sma200"] = simple_moving_average(base_df["close"], self.PERIOD)
        if not trend_one_df.empty:
            trend_one_df["hma200"] = hull_moving_average(trend_one_df["close"], self.PERIOD)
        if not trend_two_df.empty:
            trend_two_df["hma200"] = hull_moving_average(trend_two_df["close"], self.PERIOD)

        view_df["sma200_view"] = simple_moving_average(view_df["close"], self.PERIOD)

        merged = self._merge_trend_frames(base_df, trend_one_df, trend_two_df)
        evaluations, entries = self._evaluate_entries(merged)
        latest_signal = evaluations[-1] if evaluations else None
        aligned_entries = self._align_entries(entries, view_df, view_timeframe)

        payload = {
            "symbol": symbol.code,
            "timeframe": view_timeframe,
            "candles": self._serialize_candles(view_df),
            "sma200": self._serialize_indicator(view_df, "sma200_view"),
            "hma200": {
                self.TREND_TIMEFRAME_ONE: self._serialize_indicator(trend_one_df, "hma200"),
                self.TREND_TIMEFRAME_TWO: self._serialize_indicator(trend_two_df, "hma200"),
            },
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

    def _evaluate_entries(self, merged: pd.DataFrame):
        entries: List[Dict] = []
        evaluations: List[Dict] = []
        previous_long = False
        previous_short = False

        for row in merged.itertuples():
            sma = getattr(row, "sma200")
            if pd.isna(sma):
                previous_long = False
                previous_short = False
                continue

            price_5m = float(row.close)
            hma_1h = getattr(row, "hma200_1h")
            hma_4h = getattr(row, "hma200_4h")

            hma_1h = None if pd.isna(hma_1h) else float(hma_1h)
            hma_4h = None if pd.isna(hma_4h) else float(hma_4h)

            cond_5m_long = price_5m > float(sma)
            cond_5m_short = price_5m < float(sma)
            cond_1h_long = hma_1h is not None and price_5m > hma_1h
            cond_1h_short = hma_1h is not None and price_5m < hma_1h
            cond_4h_long = hma_4h is not None and price_5m > hma_4h
            cond_4h_short = hma_4h is not None and price_5m < hma_4h

            should_long = cond_5m_long and cond_1h_long and cond_4h_long
            should_short = cond_5m_short and cond_1h_short and cond_4h_short

            timestamp_iso = row.timestamp.isoformat()
            evaluations.append(
                {
                    "time": timestamp_iso,
                    "should_enter": should_long,
                    "should_enter_long": should_long,
                    "should_enter_short": should_short,
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

            if should_long and not previous_long:
                entries.append({"timestamp": row.timestamp.to_pydatetime(), "direction": "long"})
            if should_short and not previous_short:
                entries.append({"timestamp": row.timestamp.to_pydatetime(), "direction": "short"})

            previous_long = should_long
            previous_short = should_short

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
        return min(base, 20000)

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
                }
            )
        return aligned
