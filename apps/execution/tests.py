from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.exchanges.models import ExchangeAccount
from apps.strategies.models import Strategy

from .models import Bot


class BotAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="executor", email="executor@example.com", password="secret123"
        )
        self.client.force_authenticate(self.user)
        self.exchange = ExchangeAccount.objects.create(
            owner=self.user,
            name="Binance Spot",
            exchange_id="binance",
            api_key="demo",
            api_secret="demo",
        )
        self.strategy = Strategy.objects.create(
            owner=self.user,
            name="momentum",
            slug="momentum",
            description="Basic momentum strategy",
            version="0.1.0",
            config={"timeframe": "1h"},
        )
        self.bot = Bot.objects.create(
            name="momentum-bot",
            strategy=self.strategy,
            exchange_account=self.exchange,
            quote_universe=["BTC/USDT", "ETH/USDT"],
        )

    def test_start_bot_action(self):
        url = reverse("bot-start", args=[self.bot.id])
        with mock.patch("apps.execution.views.start_bot_task.delay") as mocked:
            response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mocked.assert_called_once_with(str(self.bot.id))
