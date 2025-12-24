from datetime import datetime

from django.utils.dateparse import parse_datetime
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Candle, Symbol, Divergence
from .serializers import CandleSerializer, SymbolSerializer, DivergenceSerializer


class SymbolViewSet(viewsets.ModelViewSet):
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CandleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Candle.objects.select_related("symbol").all()
    serializer_class = CandleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        symbol_code = self.request.query_params.get("symbol")
        timeframe = self.request.query_params.get("timeframe")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        limit = self.request.query_params.get("limit")

        if symbol_code:
            qs = qs.filter(symbol__code__iexact=symbol_code)
        if timeframe:
            qs = qs.filter(timeframe=timeframe)
        if start:
            start_dt = self._parse_dt(start)
            qs = qs.filter(timestamp__gte=start_dt)
        if end:
            end_dt = self._parse_dt(end)
            qs = qs.filter(timestamp__lte=end_dt)
        qs = qs.order_by("timestamp")
        if limit:
            try:
                limit_value = int(limit)
            except ValueError as exc:
                raise ValidationError("limit must be an integer") from exc
            qs = qs[:limit_value]
        return qs

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        parsed = parse_datetime(value)
        if parsed is None:
            raise ValidationError(f"Invalid datetime format: {value}")
        return parsed


class DivergenceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for retrieving divergences."""
    
    queryset = Divergence.objects.select_related("symbol").all()
    serializer_class = DivergenceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        symbol_code = self.request.query_params.get("symbol")
        timeframe = self.request.query_params.get("timeframe")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        divergence_type = self.request.query_params.get("type")
        show_all_timeframes = self.request.query_params.get("show_all_timeframes", "false").lower() == "true"

        if symbol_code:
            qs = qs.filter(symbol__code__iexact=symbol_code)
        
        if timeframe and not show_all_timeframes:
            qs = qs.filter(timeframe=timeframe)
        
        if divergence_type:
            qs = qs.filter(divergence_type=divergence_type)
        
        if start:
            start_dt = self._parse_dt(start)
            # Only show divergences that start within the visible range
            qs = qs.filter(start_timestamp__gte=start_dt)
        
        if end:
            end_dt = self._parse_dt(end)
            # Only show divergences that end within the visible range
            qs = qs.filter(end_timestamp__lte=end_dt)
        
        # Only show complete divergences (both start and end points visible)
        if start and end:
            start_dt = self._parse_dt(start)
            end_dt = self._parse_dt(end)
            qs = qs.filter(
                start_timestamp__gte=start_dt,
                end_timestamp__lte=end_dt
            )
        
        return qs.order_by("start_timestamp")

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        parsed = parse_datetime(value)
        if parsed is None:
            raise ValidationError(f"Invalid datetime format: {value}")
        return parsed
