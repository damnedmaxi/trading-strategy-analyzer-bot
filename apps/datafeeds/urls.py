from rest_framework.routers import DefaultRouter

from .views import CandleViewSet, SymbolViewSet, DivergenceViewSet

router = DefaultRouter()
router.register(r"symbols", SymbolViewSet, basename="datafeed-symbol")
router.register(r"candles", CandleViewSet, basename="datafeed-candle")
router.register(r"divergences", DivergenceViewSet, basename="datafeed-divergence")

urlpatterns = router.urls
