from __future__ import annotations

import logging
from datetime import datetime

from celery import shared_task

from .models import Symbol
from .services import fetch_ohlcv, store_candles

logger = logging.getLogger(__name__)


@shared_task(name="datafeeds.fetch_ohlcv")
def fetch_ohlcv_task(symbol_code: str, timeframe: str, limit: int = 500, since: str | None = None) -> int:
    symbol = Symbol.objects.filter(code__iexact=symbol_code).first()
    if symbol is None:
        logger.error("Symbol %s not found", symbol_code)
        return 0

    since_ms = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            since_ms = int(since_dt.timestamp() * 1000)
        except ValueError:
            logger.warning("Invalid since datetime '%s'; ignoring", since)
    payloads = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since_ms)
    count = store_candles(symbol, timeframe=timeframe, candles=payloads)
    return count
