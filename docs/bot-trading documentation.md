# Bot Trading – Documentation Central

# ##############################################################################################################################################################################################
## 1 Resumen rápido y requisitos GENERALES ##########

- **Stack principal:** Django + DRF, Channels, Celery, PostgreSQL, Redis (opcional en dev), Pandas/NumPy, React + Vite (Lightweight Charts) para la UI.
- **Python:** 3.11+. Instala dependencias dentro del `venv` con `pip install -r requirements.txt`.
- **Base de datos:** PostgreSQL 13+ (o lo que ya tengas mientras uses el motor `postgresql`).
- **Redis:** necesario para producción (Channels/Celery). En desarrollo podemos saltarlo o usar modo en memoria (ver sección de servicios).
- **Frontend:** Node 20.x (ideal 20.19+) para Vite. El proyecto está en `frontend/`.

## . Arquitectura y responsabilidades clave

- **Backend REST (Django + DRF):** expone endpoints para exchanges, estrategias, cuentas, métricas y datafeeds.
- **Channels (ASGI):** WebSockets para eventos en vivo (estado de bots, replay de backtests).
- **Celery:** tareas de ingestión (ccxt), ejecución de bots, futuros backtests. Puede correrse en modo memoria para dev, pero brilla con Redis.
- **PostgreSQL:** almacena usuarios, bots, estrategias, velas y resultados.
- **Pandas/NumPy:** cálculo de indicadores (SMA, HMA) y helpers vectorizados.
- **Frontend React (Vite + Lightweight Charts):** playback visual con velas e indicadores SMA200/HMA200, controles para play/pause, velocidad, cambio de timeframe y filtros de fechas.

## REPO:
Estructura base del repo:
```
apps/
  exchanges/   # credenciales de exchanges y rate limits
  strategies/  # estrategias, indicadores (SMA/HMA), señales long/short
  execution/   # modelo Bot, celery tasks, endpoints start/stop
  risk/        # perfil de riesgo por usuario
  analytics/   # endpoints para dashboards y KPIs
  datafeeds/   # símbolos y velas OHLCV persistidas (ccxt)
config/        # settings, routing, celery, asgi
frontend/      # React + Vite + Lightweight Charts  (visualizador de velas con playback)
docs/          # documentación adicional (estrategias, etc.)
manage.py      # comandos Django
requirements.txt
```

Referencias útiles

- `apps.exchanges`: gestiona cuentas y credenciales de exchanges (CCXT, llaves API).
- `apps/strategies/indicators.py` y `signals.py`: lógica SMA/HMA + señales long/short.
- `apps/datafeeds/services.py`: fetch/store de ccxt.
- `apps/execution/tasks.py`: ejemplo de tareas Celery que actualizan estado de bots y notifican vía Channels.
- `frontend/src/App.tsx`: compositor de UI React, fetch de velas y playback.
- `docs/strategies/hma_sma_strat.md`: descripción detallada de la estrategia.


## 2 Variables de entorno y archivos .env ##########

1. Copiá `.env.example` a `.env` y ajustá los datos reales.
   ```bash
   cp .env.example .env
   ```
2. Claves importantes (todas tienen defaults razonables para local):
   - `DJANGO_DB_*`: credenciales de Postgres.
   - `CHANNEL_LAYER_BACKEND`: `redis` (prod) o `memory` (dev sin Redis).
   - `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND`: por defecto apuntan a Redis. Para pruebas rápidas sin Redis, podés setear `memory://` (ver sección 4.2).
   - `CORS_ALLOWED_ORIGINS`: URLs del frontend (por defecto `http://localhost:5173`).
   - `CORS_ALLOW_CREDENTIALS`: mantenla en `True` si necesitás cookies/sesiones cruzadas.

## 3. Comandos habituales (con comentarios coloquiales) ##########

```bash
# 1) Migraciones – la DB tiene que saber qué tablas crear
python manage.py migrate

# 2) Arrancar el server Django (API + Channels cuando uses memory layer)
python manage.py runserver

# 3) Worker Celery – hace magia asíncrona (ingesta, backtests, etc.)
celery -A config worker -l info

# 4) Scheduler opcional – ideal para jobs recurrentes (descargar datos cada hora)
celery -A config beat -l info

# 5) Bajar velas OHLCV vía ccxt y guardarlas en Postgres
python manage.py fetch_ohlcv BTCUSDT 1h --limit 1000 --base BTC --quote USDT

# script masivo:
python apps/datafeeds/scripts/fetch_multi_timeframes.py \
  BTCUSDT \
  --base BTC \
  --quote USDT \
  --timeframes 5m 1h 4h \
  --start 2025-01-01 \
  --end 2025-12-01 \
  --limit 1000 \
  --exchange binance

1m - 1 minuto
5m - 5 minutos
15m - 15 minutos
30m - 30 minutos
1h - 1 hora
4h - 4 horas
1d - 1 día (no d)
1w - 1 semana
1M - 1 mes

# 6) Frontend React – recuerda levantar primero el backend
cd frontend && npm install
cd frontend && npm run dev
```

# ###############################################################################################################################################################################################

## 4. Cómo levantar servicios (dev y prod)

### 4.1. Sin Redis (solo para jugar un rato)
- Setea `CHANNEL_LAYER_BACKEND=memory` en `.env`. Channels usará un canal en memoria (bien para dev, no escala).
- **No levantes Celery** o, si necesitás probar algo puntual, usá modo memoria:
  ```env
  CELERY_BROKER_URL=memory://
  CELERY_RESULT_BACKEND=cache+memory://
  ```
  ```bash
  celery -A config worker -l info -P solo    ################
  ```
  > Esto funciona en single-process, sin persistencia. Apenas cierres la terminal, chau tareas. Perfecto para demos o experimentos rápidos.

### 4.2. Con Redis (modo recomendado / producción)
- Levantá Redis:
  ```bash
  # macOS con Homebrew
  brew services start redis
  # ó Docker
  docker run -p 6379:6379 redis:7-alpine
  ```
- Asegurate de tener `CHANNEL_LAYER_BACKEND=redis` y los `CELERY_*` apuntando al mismo host.
- Luego encendé Django, el worker y el beat (ver comandos de la sección 3).
- Redis te da resiliencia y permite múltiples workers Celery + Channels con WebSockets reales.

## . Tips de producción:

- **Redis obligatorio:** para Channels + Celery en serio. Considera instancias administradas o contenedores redundantes.
- **ASGI server:** usa `daphne` o `uvicorn/gunicorn` según prefieras. Recuerda correr al menos un worker Celery (o más según carga).
- **Seguridad:** guarda API keys cifradas; piensa en Vault, AWS Secrets Manager, etc. para credenciales.
- **Monitoreo:** integra logs estructurados, Prometheus/Grafana o APM a gusto.
- **CI/CD:** automatiza migraciones y despliegues; prepara scripts para descargar data histórica antes del go-live.

# ###############################################################################################################################################################################################

## 5. Ingesta de datos OHLCV (ccxt + datafeeds)

1. **Registrar símbolo (si no existe)** – el comando lo crea automáticamente si le das `--base` y `--quote`.
   ```bash
   python manage.py fetch_ohlcv ETHUSDT 1h --limit 1000 --base ETH --quote USDT
   ```
   - Guarda registros en `apps.datafeeds.models.Candle`.
   - Tené en cuenta que las timestamps quedan en UTC y listo para indicadores.
2. **Consumo vía API**
   - Velas puras: `GET /api/datafeeds/candles/?symbol=ETHUSDT&timeframe=1h&limit=500`.
   - Evaluar la estrategia SMA/HMA: `GET /api/strategies/hma-sma/run/?symbol=ETHUSDT&timeframe=1h&limit=500` devuelve las velas del timeframe solicitado, la SMA200 de ese timeframe, las HMA200 (1h/4h) y los puntos donde se dispararía una entrada (agregados desde la serie base de 5m).
3. **Series mínimas** – recordá bajar al menos 200 velas para que SMA/HMA 200 tenga sentido.


# ###############################################################################################################################################################################################

## 7. Flujo de backtesting / testing manual

1. **Descargar/actualizar velas** con el comando ccxt (o Celery task `datafeeds.fetch_ohlcv_task`).
2. **Consultar datos** desde Django shell, scripts o API y ejecuta `evaluate_long_signal` / `evaluate_short_signal` para generar señales.
3. **Backtesting batch** (idea típica): crear una tarea Celery que lea velas, ejecute la estrategia y guarde trades en una tabla `backtest_runs`. Puedes dispararla manualmente o vía `celery beat`.
4. **Dashboard React**: `npm run dev` y abre `http://localhost:5173`. Seleccioná símbolo y timeframe, presioná “Reload data” y usá los controles de reproducción.
   - El frontend consulta `GET /api/strategies/hma-sma/run/?symbol=…&timeframe=…` y dibuja la SMA200 del timeframe visible, las HMA200 (1h/4h) cerradas más recientes y las flechas `LONG`/`SHORT`. Si la señal se calculó en 5 m, la flecha se proyecta sobre la vela equivalente del timeframe seleccionado.
   - El endpoint también devuelve `should_enter_long` y `should_enter_short`, de modo que la UI muestra cuándo hay setup alcista o bajista activo.
   - El slider permite pausar, avanzar paso a paso o cambiar la velocidad; el panel lateral muestra si, en la vela actual, la condición sigue activa.
5. **Sin Redis?** Podés usar el frontend igual; sólo necesitas que el API responda a las peticiones REST. Si querés WebSockets o Celery en serio, reactivá Redis.



# ###############################################################################################################################################################
# ###############################################################################################################################################################
# ###############################################################################################################################################################
# ###############################################################################################################################################################

## 10. Mapa mental: módulos y flujo de llamadas

```
                   ┌────────────────────────────────────────────────┐
                   │                Django Backend                  │
                   ├────────────────────────────────────────────────┤
                   │                                                │
                   │  ┌──────────────┐                              │
   Frontend (React) │  │ config/     │   carga settings, URLs,      │
  ──────────────────┼─▶│ settings.py │◀── Celery config             │
                   │  └─────▲────────┘                              │
                   │        │                                       │
                   │  ┌─────┴────────┐                              │
                   │  │ config/urls  │──► rutea /api/...            │
                   │  └─────▲────────┘                              │
                   │        │                                       │
                   │  ┌─────┴──────────┐                            │
                   │  │ apps/datafeeds │── modelos Symbol/Candle    │
                   │  │                │   └─ services.fetch_ohlcv  │
                   │  │                │   └─ management cmd + task │
                   │  └────────▲───────┘                            │
                   │           │                                    │
                   │  ┌────────┴────────┐                           │
                   │  │ apps/strategies │── modelos Strategy        │
                   │  │                │   └─ views.HMASMAStrategy  │
                   │  │                │      ↳ usa datafeeds.Candle│
                   │  │                │      ↳ aplica HMA/SMA      │
                   │  └────────▲────────┘                           │
                   │           │                                    │
                   │  ┌────────┴────────┐                           │
                   │  │ apps/execution  │── Bot + tasks start/stop  │
                   │  │                │   (pendiente de integrar   │
                   │  │                │    señales y órdenes)      │
                   │  └────────┬────────┘                           │
                   │           │                                    │
                   │  ┌────────┴────────┐                           │
                   │  │ apps/analytics  │── endpoints para KPIs,    │
                   │  │                │   backtesting, dashboards │
                   │  └─────────────────┘                           │
                   │                                                │
                   └────────────────────────────────────────────────┘

Notas clave:

1. **datafeeds** es la puerta de entrada de datos históricos (Symbol/Candle). `services.fetch_ohlcv` se reutiliza tanto desde el management command como desde la tarea Celery `datafeeds.fetch_ohlcv_task`.
2. **strategies** encapsula la lógica de SMA/HMA. El endpoint `HMASMAStrategyRunView`:
   - Lee velas de `datafeeds.Candle`.
   - Calcula SMA200 de 5m y HMA200 cerradas de 1h/4h.
   - Emite timeline + puntos de entrada (long/short).
   - La respuesta alimenta el frontend para pintado de velas y flechas.
3. **execution** manejará bots en vivo (Celery tasks `start_bot`/`stop_bot`). A futuro conectará la salida de `strategies` con la colocación de órdenes reales.
4. **analytics** será el punto central para KPIs, backtests y dashboards (por ahora muestra mocks).
5. **Frontend (React + Vite)** consume:
   - `/api/datafeeds/candles/` para velas “puras”.
   - `/api/strategies/hma-sma/run/` para estrategia + señales.
   - Lightweight Charts dibuja SMA/HMA y markers; React Query mantiene el estado.

Cadena típica:

```
React (App.tsx) ──▶ /api/strategies/hma-sma/run/
   └─ recibe velas + SMA + HMA + entries
   └─ CandlestickChart muestra overlays y flechas

fetch_multi_timeframes.py ──▶ services.fetch_ohlcv ─▶ Candle.bulk_create
   (opcional Celery task)          │
                                   └─ datos quedan listos para HMASMAStrategy
```

Esta vista rápida ayuda a navegar el repo: si buscas dónde se calcula la HMA dinámica, ve a `apps/strategies/views.py`; si querés ajustar la ingesta, visita `apps/datafeeds/services.py` o el script de `scripts/`. 
```



