import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from .models import Bot
from .services import notify_bot_update

logger = logging.getLogger(__name__)


@shared_task(name="execution.start_bot")
def start_bot_task(bot_id: str) -> None:
    try:
        bot = Bot.objects.get(id=bot_id)
    except Bot.DoesNotExist:
        logger.error("Bot %s not found when attempting start.", bot_id)
        return

    bot.status = Bot.Status.RUNNING
    bot.last_heartbeat_at = timezone.now()
    bot.save(update_fields=["status", "last_heartbeat_at"])
    logger.info("Bot %s marked as running at %s", bot.id, datetime.utcnow())
    notify_bot_update(
        str(bot.id),
        {
            "status": bot.status,
            "last_heartbeat_at": bot.last_heartbeat_at.isoformat(),
        },
    )
    # TODO: Kick off real trading loop here.


@shared_task(name="execution.stop_bot")
def stop_bot_task(bot_id: str) -> None:
    try:
        bot = Bot.objects.get(id=bot_id)
    except Bot.DoesNotExist:
        logger.error("Bot %s not found when attempting stop.", bot_id)
        return

    bot.status = Bot.Status.STOPPED
    bot.save(update_fields=["status"])
    logger.info("Bot %s marked as stopped", bot.id)
    notify_bot_update(
        str(bot.id),
        {
            "status": bot.status,
            "last_heartbeat_at": bot.last_heartbeat_at.isoformat()
            if bot.last_heartbeat_at
            else None,
        },
    )
    # TODO: Gracefully stop trading loop and cleanup resources.
