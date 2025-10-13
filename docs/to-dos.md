# ###############################################################################################################################################################
# ###############################################################################################################################################################
# ###############################################################################################################################################################
# ###############################################################################################################################################################
# ###############################################################################################################################################################

## 11. To‑Do (roadmap)

1. **Cierre de trades / PnL**
   - Definir criterios de salida (take profit, stop loss, trailing).
   - Registrar PnL por operación y almacenarlo en una tabla (`trade_logs` / `backtest_runs`).
   - Exponer resúmenes en `/api/analytics/` y mostrarlos en el frontend (acumulado, drawdown, win-rate).

2. **Backtesting automático**
   - Tarea Celery que ejecute la estrategia sobre periodos/rangos sin UI.
   - Guardar resultados (por símbolo, timeframe, version/tag de estrategia).
   - API + UI para comparar runs históricos (gráficos, ranking de versiones).

3. **Versionado de estrategias**
   - Guardar hash/config de cada ejecución.
   - Permitir rollback o comparación entre versiones (metadatos en `apps.strategies`).

4. **Integración live / Alerts**
   - Conectar señales a `apps.execution` para envío de órdenes (paper o real).
   - Añadir notificaciones externas (Telegram, webhook) cuando aparezca una señal.

5. **Frontend**
   - Panel de métricas (P&L, drawdown, nº de trades).
   - Tabla sincronizada de operaciones.
   - Filtros adicionales (volatilidad, indicadores extra, overlays custom).

6. **Data & Infra**
   - Scheduler recurrente (Celery beat / cron) para descarga de velas y evaluación periódica.
   - Opcional: persistir histórico en Parquet y cargarlo bajo demanda.
   - Optimizar índices en `Candle` (symbol + timeframe + timestamp) para escalar.

7. **Testing / QA**
   - Unit tests para nuevas reglas de salida y PnL.
   - Tests E2E del endpoint `/api/strategies/hma-sma/run/` (performance, consistencia).
   - Tests de frontend (vitest/Playwright) para validar markers y estados LONG/SHORT.

8. **Documentación**
   - Guía de onboarding (instalación, ingestión, primer run).
   - Ejemplos de `.env` y scripts comunes.
   - Checklists para despliegue (Redis, Celery, Node, etc.).

9. **Sugerencias extras**
   - Permitir múltiples estrategias (RSI, EMAs, etc.) con endpoints parametrizables.
   - Abstraer la capa de señales para reutilizarla en ejecución y backtesting.
   - Añadir canal WebSocket (Channels) para replay en vivo sin reload.

Actualizá este listado para llevar control del desarrollo: tilda lo completado, añade ideas nuevas y prioriza según lo que necesites atacar primero.

################################################################################################################################################################