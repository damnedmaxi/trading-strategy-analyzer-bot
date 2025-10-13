from rest_framework import serializers

from .models import RiskProfile


class RiskProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskProfile
        fields = [
            "owner",
            "max_concurrent_positions",
            "max_capital_per_position_pct",
            "daily_loss_limit_pct",
            "max_total_drawdown_pct",
            "updated_at",
        ]
        read_only_fields = ("owner", "updated_at")
