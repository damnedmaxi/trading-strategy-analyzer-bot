from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ExchangeAccount


class ExchangeAccountAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", email="tester@example.com", password="secret123"
        )
        self.client.force_authenticate(self.user)

    def test_create_account(self):
        url = reverse("exchange-account-list")
        payload = {
            "name": "Spot Binance",
            "exchange_id": "binance",
            "api_key": "demo",
            "api_secret": "demo-secret",
            "rate_limit_per_minute": 120,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExchangeAccount.objects.count(), 1)
