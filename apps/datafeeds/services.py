from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, List

import ccxt

from .models import Candle, Symbol

logger = logging.getLogger(__name__)


@dataclass
class CandlePayload:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def fetch_ohlcv(symbol: Symbol, timeframe: str, limit: int = 500, since: int | None = None) -> List[CandlePayload]:
    exchange_id = symbol.exchange.lower()
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"Exchange '{exchange_id}' is not supported by ccxt")
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})

    pair = symbol.ccxt_pair
    logger.info("Fetching %s %s candles (limit=%s, since=%s)", pair, timeframe, limit, since)
    raw = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit, since=since)
    payloads: List[CandlePayload] = []
    for ts, o, h, l, c, v in raw:
        payloads.append(
            CandlePayload(
                timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
                open=Candle.normalize_value(o),
                high=Candle.normalize_value(h),
                low=Candle.normalize_value(l),
                close=Candle.normalize_value(c),
                volume=Candle.normalize_value(v),
            )
        )
    return payloads


def store_candles(symbol: Symbol, timeframe: str, candles: Iterable[CandlePayload], source: str = "ccxt") -> int:
    objs = []
    for candle in candles:
        objs.append(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=candle.timestamp,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                source=source,
            )
        )
    if not objs:
        return 0
    inserted = Candle.objects.bulk_create(objs, ignore_conflicts=True)
    logger.info("Inserted %s candles for %s %s", len(inserted), symbol.code, timeframe)
    return len(inserted)
