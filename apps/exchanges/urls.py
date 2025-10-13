from rest_framework.routers import DefaultRouter

from .views import ExchangeAccountViewSet

router = DefaultRouter()
router.register(r"accounts", ExchangeAccountViewSet, basename="exchange-account")

urlpatterns = router.urls
