from django.conf import settings
from django.db import models


class RiskProfile(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="risk_profile",
    )
    max_concurrent_positions = models.PositiveIntegerField(default=5)
    max_capital_per_position_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        help_text="Percentage of available capital per position.",
    )
    daily_loss_limit_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.0,
        help_text="Kill switch threshold for daily drawdown.",
    )
    max_total_drawdown_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=25.0,
        help_text="Circuit breaker threshold for overall drawdown.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Risk profile for {self.owner}"
