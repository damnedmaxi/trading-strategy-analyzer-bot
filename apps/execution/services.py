import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def notify_bot_update(bot_id: str, payload: Dict[str, Any]) -> None:
    """
    Pushes a bot state payload to any subscribed websocket consumers.
    Can be called from synchronous contexts (Celery tasks, Django signals).
    """

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer not configured; skipping websocket push.")
        return

    group_name = f"bot_{bot_id}"

    try:
        async_to_sync(channel_layer.group_send)(
            group_name, {"type": "bot_update", "payload": payload}
        )
    except Exception as exc:
        logger.exception("Failed to publish websocket update for bot %s: %s", bot_id, exc)
