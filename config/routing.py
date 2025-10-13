from django.urls import path

from apps.execution import routing as execution_routing

websocket_urlpatterns = [
    *execution_routing.websocket_urlpatterns,
]
