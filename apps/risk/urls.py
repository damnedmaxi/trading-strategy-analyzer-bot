from django.urls import path

from .views import RiskProfileView

urlpatterns = [
    path("profile/", RiskProfileView.as_view(), name="risk-profile"),
]
