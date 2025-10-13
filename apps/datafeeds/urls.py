from rest_framework.routers import DefaultRouter

from .views import CandleViewSet, SymbolViewSet

router = DefaultRouter()
router.register(r"symbols", SymbolViewSet, basename="datafeed-symbol")
router.register(r"candles", CandleViewSet, basename="datafeed-candle")

urlpatterns = router.urls
