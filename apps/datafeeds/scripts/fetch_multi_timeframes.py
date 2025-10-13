# Ejemplo de uso:
# python apps/datafeeds/scripts/fetch_multi_timeframes.py \
#   BTCUSDT \
#   --base BTC \
#   --quote USDT \
#   --timeframes 5m 1h 4h \
#   --start 2025-01-01 \
#   --end 2025-12-01 \
#   --limit 1000 \
#   --exchange binance



# scripts/fetch_multi_timeframes.py
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import django

# Asegurate de ejecutar este script desde cualquier lugar agregando la raíz al sys.path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.datafeeds.models import Candle, Symbol
from apps.datafeeds.services import fetch_ohlcv, store_candles  # noqa: E402


def parse_iso(value: str) -> datetime:
    """
    Acepta formatos ISO con o sin 'Z'. Si viene sin tz, asumimos UTC.
    """
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ensure_symbol(symbol_code: str, base: str, quote: str, exchange: str, ccxt_symbol: str) -> Symbol:
    symbol, created = Symbol.objects.get_or_create(
        code=symbol_code.upper(),
        defaults={
            "base_asset": base.upper(),
            "quote_asset": quote.upper(),
            "exchange": exchange,
            "ccxt_symbol": ccxt_symbol or f"{base.upper()}/{quote.upper()}",
        },
    )
    if not created:
        updates = {}
        if exchange:
            updates["exchange"] = exchange
        if ccxt_symbol:
            updates["ccxt_symbol"] = ccxt_symbol
        if updates:
            for key, value in updates.items():
                setattr(symbol, key, value)
            symbol.save(update_fields=list(updates.keys()))
    return symbol


def paginate_fetch(symbol: Symbol, timeframe: str, start: datetime, end: datetime, batch_size: int) -> None:
    since_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    total_inserted = 0

    while since_ms < end_ms:
        payloads = fetch_ohlcv(symbol, timeframe=timeframe, limit=batch_size, since=since_ms)
        if not payloads:
            break

        inserted = store_candles(symbol, timeframe, payloads)
        total_inserted += inserted

        last_ts = payloads[-1].timestamp
        since_ms = int(last_ts.timestamp() * 1000) + 1
        if last_ts.timestamp() * 1000 >= end_ms:
            break

    print(f"[{symbol.code} {timeframe}] Insertadas {total_inserted} velas")


def main():
    parser = argparse.ArgumentParser(description="Descargar múltiples timeframes de ccxt y almacenarlos en datafeeds.Candle")
    parser.add_argument("symbol", help="Código interno del símbolo (e.g. BTCUSDT)")
    parser.add_argument("--base", required=True, help="Asset base (e.g. BTC)")
    parser.add_argument("--quote", required=True, help="Asset quote (e.g. USDT)")
    parser.add_argument(
        "--timeframes", nargs="+", required=True,
        help="Lista de timeframes aceptados por ccxt (5m, 30m, 1h, 4h, 1d, ...)",
    )
    parser.add_argument("--start", required=True, help="Fecha inicial ISO (e.g. 2024-01-01 o 2024-01-01T00:00:00Z)")
    parser.add_argument("--end", required=True, help="Fecha final ISO (e.g. 2024-03-01)")
    parser.add_argument("--limit", type=int, default=500, help="Velas por request (depende del exchange; Binance máx. 1000)")
    parser.add_argument("--exchange", default="binance", help="Exchange ccxt (default: binance)")
    parser.add_argument("--ccxt-symbol", dest="ccxt_symbol", help="Par ccxt, si difiere del código (e.g. BTC/USDT)")

    args = parser.parse_args()

    start_dt = parse_iso(args.start)
    end_dt = parse_iso(args.end)
    if end_dt <= start_dt:
        raise ValueError("La fecha final debe ser mayor a la inicial")

    symbol = ensure_symbol(
        symbol_code=args.symbol,
        base=args.base,
        quote=args.quote,
        exchange=args.exchange,
        ccxt_symbol=args.ccxt_symbol,
    )

    for timeframe in args.timeframes:
        if timeframe not in dict(Candle.Timeframe.choices):
            print(f"⚠️  Timeframe '{timeframe}' no está listado en Candle.Timeframe.choices; igual se intentará.")
        paginate_fetch(symbol, timeframe, start_dt, end_dt, batch_size=args.limit)


if __name__ == "__main__":
    main()
