from rest_framework import generics, permissions

from .models import RiskProfile
from .serializers import RiskProfileSerializer


class RiskProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = RiskProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = RiskProfile.objects.get_or_create(owner=self.request.user)
        return profile
