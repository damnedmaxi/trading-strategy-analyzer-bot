from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Strategy(models.Model):
    """
    Stores metadata and parameters for a trading strategy definition.
    Config can include indicator parameters, universe filters, and risk settings.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="strategies",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="0.1.0")
    config = models.JSONField(default=dict, blank=True)
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("owner", "name", "version")

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.owner_id}-{self.name}-{self.version}")
        super().save(*args, **kwargs)
