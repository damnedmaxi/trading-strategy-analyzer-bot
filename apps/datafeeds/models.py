from __future__ import annotations

from decimal import Decimal

from django.db import models


class Symbol(models.Model):
    """Represents a tradable pair in a given exchange."""

    code = models.CharField(max_length=40, unique=True, help_text="Symbol code e.g. BTCUSDT")
    ccxt_symbol = models.CharField(
        max_length=40,
        help_text="Trading pair format used by ccxt (e.g. BTC/USDT)",
        blank=True,
    )
    base_asset = models.CharField(max_length=20)
    quote_asset = models.CharField(max_length=20)
    exchange = models.CharField(max_length=50, default="binance")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} ({self.exchange})"

    @property
    def ccxt_pair(self) -> str:
        return self.ccxt_symbol or f"{self.base_asset}/{self.quote_asset}"


class Candle(models.Model):
    class Timeframe(models.TextChoices):
        M5 = "5m", "5 Minutes"
        M30 = "30m", "30 Minutes"
        H1 = "1h", "1 Hour"
        H4 = "4h", "4 Hours"
        D1 = "1d", "1 Day"

    symbol = models.ForeignKey(Symbol, related_name="candles", on_delete=models.CASCADE)
    timeframe = models.CharField(max_length=5, choices=Timeframe.choices)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=28, decimal_places=10)
    source = models.CharField(max_length=50, default="ccxt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("symbol", "timeframe", "timestamp")
        unique_together = ("symbol", "timeframe", "timestamp")

    def __str__(self) -> str:
        return f"{self.symbol.code} {self.timeframe} @ {self.timestamp.isoformat()}"

    @classmethod
    def normalize_value(cls, value: float | Decimal | str) -> Decimal:
        return Decimal(str(value))
