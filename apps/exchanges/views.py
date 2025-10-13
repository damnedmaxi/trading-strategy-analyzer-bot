from rest_framework import permissions, viewsets

from .models import ExchangeAccount
from .serializers import ExchangeAccountSerializer


class ExchangeAccountViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return ExchangeAccount.objects.all()
        return ExchangeAccount.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
