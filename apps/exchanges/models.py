from django.conf import settings
from django.db import models


class ExchangeAccount(models.Model):
    """
    Represents credentials and configuration for a single exchange account.
    API secrets should be stored encrypted in production (e.g. Hashicorp Vault).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exchange_accounts",
    )
    name = models.CharField(max_length=100)
    exchange_id = models.CharField(max_length=50, help_text="CCXT exchange identifier.")
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    password = models.CharField(
        max_length=255,
        blank=True,
        help_text="Some exchanges require an additional password or passphrase.",
    )
    is_testnet = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("owner", "name")

    def __str__(self) -> str:
        return f"{self.owner}::{self.name} ({self.exchange_id})"
