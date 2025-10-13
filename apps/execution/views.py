from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Bot
from .serializers import BotSerializer
from .tasks import start_bot_task, stop_bot_task


class BotViewSet(viewsets.ModelViewSet):
    serializer_class = BotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Bot.objects.select_related("strategy", "exchange_account")

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(strategy__owner=self.request.user)

    def perform_create(self, serializer):
        strategy = serializer.validated_data["strategy"]
        exchange = serializer.validated_data["exchange_account"]
        if not self.request.user.is_superuser and strategy.owner != self.request.user:
            raise PermissionDenied("You do not own the selected strategy.")
        if not self.request.user.is_superuser and exchange.owner != self.request.user:
            raise PermissionDenied("You do not own the selected exchange account.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        bot = self.get_object()
        start_bot_task.delay(str(bot.id))
        return Response({"detail": "Bot start requested."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        bot = self.get_object()
        stop_bot_task.delay(str(bot.id))
        return Response({"detail": "Bot stop requested."}, status=status.HTTP_202_ACCEPTED)
