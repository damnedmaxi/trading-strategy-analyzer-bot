from datetime import datetime, timezone

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Candle, Symbol


class DatafeedAPITests(APITestCase):
    def setUp(self):
        self.symbol = Symbol.objects.create(
            code="ETHUSDT",
            ccxt_symbol="ETH/USDT",
            base_asset="ETH",
            quote_asset="USDT",
        )
        Candle.objects.create(
            symbol=self.symbol,
            timeframe=Candle.Timeframe.H1,
            timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            open=1000,
            high=1100,
            low=990,
            close=1050,
            volume=10,
        )

    def test_symbol_list(self):
        url = reverse("datafeed-symbol-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_candle_filter(self):
        url = reverse("datafeed-candle-list")
        response = self.client.get(url, {"symbol": "ETHUSDT", "timeframe": "1h"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data[0]["close"], "1050.00000000")
