# Frontend – Strategy Visualizer

React + Vite dashboard to inspect SMA/HMA signals using lightweight-charts.

## Setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The app expects the Django backend running locally at `http://127.0.0.1:8000`. Adjust `VITE_API_BASE_URL` in `.env` if needed.

## Features

- Fetches candles from `/api/datafeeds/candles/` and symbol catalog from `/api/datafeeds/symbols/`.
- Renders candlesticks with SMA200 / HMA200 overlays.
- Playback controls (play/pause, step, seek, adjustable speed) to replay historical data.
- Filter by timeframe, limit, and optional date range.

## Available scripts

- `npm run dev` – start Vite dev server with hot reload.
- `npm run build` – production build.
- `npm run preview` – preview local build.
