from django.urls import path

from .views import EquityCurveView, PerformanceSummaryView

urlpatterns = [
    path("equity-curve/", EquityCurveView.as_view(), name="equity-curve"),
    path("summary/", PerformanceSummaryView.as_view(), name="performance-summary"),
]
