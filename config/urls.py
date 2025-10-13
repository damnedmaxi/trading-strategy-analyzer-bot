from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="dashboard.html"), name="dashboard"),
    path("admin/", admin.site.urls),
    path("api/exchanges/", include("apps.exchanges.urls")),
    path("api/strategies/", include("apps.strategies.urls")),
    path("api/execution/", include("apps.execution.urls")),
    path("api/risk/", include("apps.risk.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/datafeeds/", include("apps.datafeeds.urls")),
]
