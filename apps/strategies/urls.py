from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import HMASMAStrategyRunView, StrategyViewSet

router = DefaultRouter()
router.register(r"", StrategyViewSet, basename="strategy")

urlpatterns = [
    path("hma-sma/run/", HMASMAStrategyRunView.as_view(), name="hma-sma-run"),
]

urlpatterns += router.urls
