# Bot Trading

## Objective
Platform to ingest OHLCV data, evaluate trading strategies, visualize signals and technical divergences, and monitor bot status in real time.

## Architecture (high level)
- **Backend (Django + DRF):** REST APIs for datafeeds, strategies, execution, analytics, risk, and exchanges.
- **Real time (Channels):** WebSockets for bot status updates.
- **Async processing (Celery):** candle ingestion and execution tasks.
- **Persistence (PostgreSQL):** users, strategies, bots, candles, and indicators.
- **Frontend (React + Vite):** dashboard with candle playback, SMA/HMA overlays, and divergence visualization.

Basic flow:
```
ccxt -> datafeeds (Candle/Symbol) -> strategies (SMA/HMA, divergences) -> API
                                                       |
                                                       v
                                                   frontend
```

## Tech stack
- **Backend:** Django, Django REST Framework, Channels, Celery
- **Data/indicators:** PostgreSQL, Redis (prod), Pandas, NumPy, CCXT
- **Frontend:** React, Vite, Lightweight Charts

## Key components
- `apps/datafeeds`: OHLCV ingestion and storage.
- `apps/strategies`: indicator calculation and signal generation.
- `apps/execution`: bot model and start/stop tasks.
- `apps/analytics`: KPIs/dashboards endpoints (preview).
- `apps/exchanges`: exchange accounts and credentials.
- `apps/risk`: risk profile endpoints.

## Installation (local development)
1. Requirements: Python 3.11+ and Node 20.x.
2. Create and activate a virtualenv, then install backend deps:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
4. Run migrations and start the backend:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
5. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Optional (async + websockets in dev without Redis):
- Set `CHANNEL_LAYER_BACKEND=memory` and `CELERY_BROKER_URL=memory://` / `CELERY_RESULT_BACKEND=cache+memory://` in `.env`.

## Deployment (production)
1. Set up PostgreSQL and Redis, then configure `.env` with real credentials.
2. Apply migrations:
   ```bash
   python manage.py migrate
   ```
3. Run an ASGI server for Django (e.g. `daphne` or `uvicorn`), plus Celery worker(s) and optional beat:
   ```bash
   celery -A config worker -l info
   celery -A config beat -l info
   ```
4. Build and serve the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   Serve `frontend/dist/` from your preferred web server or host it separately.

## Update trading pairs and market data
Create or update a symbol and fetch candles:
```bash
python manage.py fetch_ohlcv BTCUSDT 1h --limit 1000 --base BTC --quote USDT
```

Incremental updates using `--since` (UTC ISO datetime):
```bash
python manage.py fetch_ohlcv BTCUSDT 1h --since 2024-01-01T00:00:00
```

Batch backfill across multiple timeframes:
```bash
python apps/datafeeds/scripts/fetch_multi_timeframes.py \
  BTCUSDT \
  --base BTC \
  --quote USDT \
  --timeframes 5m 1h 4h \
  --start 2024-01-01 \
  --end 2024-12-01 \
  --limit 1000 \
  --exchange binance
```
