from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView


class EquityCurveView(APIView):
    """Returns a lightweight equity curve for dashboard previews."""

    def get(self, request):
        now = timezone.now()
        data = [
            {
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "equity": 10000 + i * 25,
            }
            for i in range(24, -1, -1)
        ]
        return Response({"equity_curve": data})


class PerformanceSummaryView(APIView):
    """Aggregate KPIs for the monitored bots."""

    def get(self, request):
        summary = {
            "total_return_pct": 12.5,
            "max_drawdown_pct": 4.2,
            "sharpe_ratio": 1.8,
            "open_positions": 3,
            "closed_positions_today": 12,
        }
        return Response(summary)
