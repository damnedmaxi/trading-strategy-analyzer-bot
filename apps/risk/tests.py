from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import RiskProfile


class RiskProfileAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="risker", email="risker@example.com", password="secret123"
        )
        self.client.force_authenticate(self.user)

    def test_get_profile_creates_default(self):
        url = reverse("risk-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RiskProfile.objects.filter(owner=self.user).count(), 1)

