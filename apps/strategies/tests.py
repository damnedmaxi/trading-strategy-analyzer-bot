from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import numpy as np
import pandas as pd
from rest_framework import status
from rest_framework.test import APITestCase

from apps.datafeeds.models import Candle, Symbol

from .models import Strategy
from .signals import evaluate_long_signal, evaluate_short_signal, latest_signal_direction


class StrategyAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="strategist", email="strategist@example.com", password="secret123"
        )
        self.client.force_authenticate(self.user)

    def test_create_strategy(self):
        url = reverse("strategy-list")
        payload = {
            "name": "rsi-reversion",
            "description": "Buy when RSI under 30, sell over 70.",
            "version": "0.1.0",
            "config": {"indicator": {"rsi_period": 14}, "timeframe": "1h"},
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Strategy.objects.count(), 1)


class StrategySignalTests(TestCase):
    def setUp(self):
        self.series_5m = self._make_series(periods=240, step=0.5, freq="5min")
        self.series_1h = self._make_series(periods=240, step=1.0, freq="1h")
        self.series_4h = self._make_series(periods=240, step=1.5, freq="4h")

    def _make_series(self, periods: int, step: float, freq: str, start: str = "2024-01-01") -> pd.Series:
        index = pd.date_range(start, periods=periods, freq=freq)
        values = 100 + step * np.arange(periods)
        return pd.Series(values, index=index, dtype=float)

    def test_long_signal_conditions_met(self):
        result = evaluate_long_signal(
            {"5m": self.series_5m, "1h": self.series_1h, "4h": self.series_4h}
        )
        self.assertTrue(result.should_enter)
        self.assertTrue(result.breakdown["1h"].condition_met)
        self.assertTrue(result.breakdown["4h"].condition_met)
        self.assertTrue(result.breakdown["5m"].condition_met)
        self.assertEqual(latest_signal_direction(result), "long")

    def test_long_signal_fails_when_macro_breaks(self):
        degraded_4h = self.series_4h.copy()
        degraded_4h.iloc[-1] = degraded_4h.mean() * 0.9
        result = evaluate_long_signal(
            {"5m": self.series_5m, "1h": self.series_1h, "4h": degraded_4h}
        )
        self.assertFalse(result.should_enter)
        self.assertFalse(result.breakdown["4h"].condition_met)
        self.assertIsNone(latest_signal_direction(result))

    def test_missing_timeframe_raises(self):
        with self.assertRaises(KeyError):
            evaluate_long_signal({"5m": self.series_5m, "1h": self.series_1h})

    def test_short_signal_conditions_met(self):
        closes = {
            "5m": self._make_series(periods=400, step=-0.2, freq="5min"),
            "1h": self._make_series(periods=260, step=-0.8, freq="1h"),
            "4h": self._make_series(periods=260, step=-1.2, freq="4h"),
        }
        result = evaluate_short_signal(closes)
        self.assertTrue(result.should_enter)
        self.assertEqual(latest_signal_direction(result), "short")


class HMASMAStrategyRunAPITests(TestCase):
    def setUp(self):
        self.symbol = Symbol.objects.create(
            code="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            exchange="binance",
        )
        base_start = datetime(2024, 1, 1, tzinfo=timezone.utc)

        for i in range(260):
            ts = base_start + timedelta(minutes=5 * i)
            price = 100 + i * 0.5
            Candle.objects.create(
                symbol=self.symbol,
                timeframe=Candle.Timeframe.M5,
                timestamp=ts,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=1,
            )

        for i in range(260):
            ts = base_start + timedelta(hours=i)
            price = 100 + i
            Candle.objects.create(
                symbol=self.symbol,
                timeframe=Candle.Timeframe.H1,
                timestamp=ts,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=1,
            )

        for i in range(260):
            ts = base_start + timedelta(hours=4 * i)
            price = 100 + i * 2
            Candle.objects.create(
                symbol=self.symbol,
                timeframe=Candle.Timeframe.H4,
                timestamp=ts,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=1,
            )

    def test_hma_sma_strategy_run_endpoint(self):
        url = reverse("hma-sma-run")
        response = self.client.get(url, {"symbol": "BTCUSDT", "limit": 250})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["symbol"], "BTCUSDT")
        self.assertGreater(len(data["candles"]), 0)
        self.assertIn("entries", data)
        self.assertIsInstance(data["entries"], list)
        if data["entries"]:
            self.assertIn("source_time", data["entries"][0])
        self.assertIn("signal_timeline", data)
        self.assertGreater(len(data["signal_timeline"]), 0)
