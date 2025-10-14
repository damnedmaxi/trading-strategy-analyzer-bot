# ###############################################################################################################################################################


## 11. To‑Do (roadmap)
# DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE 
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

# DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE 
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

8. 

------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------


## ✅ COMPLETADO - 13 Octubre 2025

### **🔴 Bug Crítico: Estado Incorrecto de Posiciones en Backend**

**Problema Identificado:**
- Las variables `previous_long` y `previous_short` se actualizaban con las **condiciones de entrada** en lugar del **estado real de la posición**
- Resultado: Las posiciones nunca se cerraban y el PnL seguía acumulando indefinidamente
- Impacto: TODOS los backtests históricos tienen métricas incorrectas

**Solución:**
- ✅ Renombrar variables a `position_long_open` y `position_short_open` para claridad
- ✅ Actualizar estado solo cuando se abre/cierra realmente una posición
- ✅ Prevenir posiciones simultáneas (LONG y SHORT al mismo tiempo)
- **Archivo:** `apps/strategies/views.py` (líneas 193-302)

**Documentación:**
- ✅ `docs/bug-critico-estado-posiciones.md` - Análisis completo del bug y corrección

**Resultado:**
- Las posiciones ahora se cierran correctamente cuando se cumplen las condiciones de salida
- El PnL se congela cuando no hay posiciones abiertas
- Las flechas de exit se generan correctamente
- Los backtests ahora son confiables

⚠️ **ACCIÓN REQUERIDA:** Re-ejecutar todos los backtests históricos importantes

---

### **Correcciones Críticas de Sincronización en Frontend**

**Problemas Diagnosticados y Resueltos:**

1. ✅ **Flechas invisibles en timeframes > 5m**
   - **Causa:** Markers usando `entry.time` en vez de `entry.sourceTime`
   - **Solución:** Cambiar todos los markers para usar el timestamp real de la señal
   - **Archivo:** `frontend/src/components/CandlestickChart.tsx`

2. ✅ **Markers sin datos subyacentes en la serie**
   - **Causa:** `markerSeries` solo tenía datos para velas del timeframe de visualización
   - **Solución:** Poblar `markerSeries` con datos para cada `sourceTime` de las entradas
   - **Archivo:** `frontend/src/components/CandlestickChart.tsx` (líneas 152-193)

3. ✅ **Órdenes que no se cerraban correctamente**
   - **Causa:** `cutoffTime` usaba inicio de vela, excluyendo entradas dentro de la vela
   - **Solución:** Calcular `cutoffTime` como inicio de próxima vela o fin de actual
   - **Archivo:** `frontend/src/App.tsx` (líneas 92-110)

**Documentación Generada:**
- ✅ `docs/frontend-diagnostico-y-mejoras.md` - Análisis completo de problemas y soluciones
- ✅ `docs/checklist-pruebas-frontend.md` - Guía de pruebas paso a paso

**Resultado:**
- Flechas ahora visibles en TODOS los timeframes (5m, 30m, 1h, 4h, 1d)
- Sincronización correcta entre órdenes abiertas/cerradas y visualización
- PnL calculado correctamente y sincronizado con las señales mostradas

---

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