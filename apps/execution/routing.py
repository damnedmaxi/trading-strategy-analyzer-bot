from django.urls import path

from .consumers import BotStatusConsumer

websocket_urlpatterns = [
    path("ws/bots/<uuid:bot_id>/status/", BotStatusConsumer.as_asgi()),
]
