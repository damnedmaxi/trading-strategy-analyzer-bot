from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from apps.datafeeds.models import Candle, Symbol
from apps.datafeeds.services import fetch_ohlcv, store_candles


class Command(BaseCommand):
    help = "Fetch OHLCV data via ccxt and persist it in the Candle table."

    def add_arguments(self, parser):
        parser.add_argument("symbol", help="Symbol code stored in the database (e.g. BTCUSDT)")
        parser.add_argument("timeframe", help="ccxt timeframe to fetch (e.g. 5m, 1h)")
        parser.add_argument("--limit", type=int, default=500, help="Number of candles to fetch")
        parser.add_argument("--since", type=str, help="ISO datetime to start from (UTC)")
        parser.add_argument("--exchange", type=str, help="Override exchange id")
        parser.add_argument("--ccxt-symbol", dest="ccxt_symbol", type=str, help="Pair for ccxt (e.g. BTC/USDT)")
        parser.add_argument("--base", dest="base_asset", type=str, help="Base asset code (BTC)")
        parser.add_argument("--quote", dest="quote_asset", type=str, help="Quote asset code (USDT)")

    def handle(self, *args, **options):
        symbol_code = options["symbol"].upper()
        timeframe = options["timeframe"]
        limit = options["limit"]
        since_str = options.get("since")
        exchange_override = options.get("exchange")
        ccxt_symbol = options.get("ccxt_symbol")
        base_asset = options.get("base_asset")
        quote_asset = options.get("quote_asset")

        symbol = Symbol.objects.filter(code__iexact=symbol_code).first()
        if symbol is None:
            if not base_asset or not quote_asset:
                raise CommandError("Symbol not found; provide --base and --quote to create it")
            symbol = Symbol.objects.create(
                code=symbol_code,
                base_asset=base_asset.upper(),
                quote_asset=quote_asset.upper(),
                exchange=exchange_override or "binance",
                ccxt_symbol=ccxt_symbol or f"{base_asset.upper()}/{quote_asset.upper()}",
            )
        else:
            if exchange_override:
                symbol.exchange = exchange_override
            if ccxt_symbol:
                symbol.ccxt_symbol = ccxt_symbol
            symbol.save(update_fields=["exchange", "ccxt_symbol"])

        if timeframe not in dict(Candle.Timeframe.choices):
            self.stdout.write(self.style.WARNING(f"Timeframe '{timeframe}' not in defaults; continuing."))

        since_ms = None
        if since_str:
            try:
                since_dt = datetime.fromisoformat(since_str)
            except ValueError as exc:
                raise CommandError(f"Invalid since datetime: {since_str}") from exc
            since_ms = int(since_dt.timestamp() * 1000)

        payloads = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since_ms)
        count = store_candles(symbol, timeframe=timeframe, candles=payloads)
        self.stdout.write(self.style.SUCCESS(f"Inserted {count} candles for {symbol.code} {timeframe}"))
