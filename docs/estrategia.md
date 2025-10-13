# Estrategia SMA/HMA 200 – Entradas Long y Short

## Resumen

La estrategia define condiciones de confirmación multiframe utilizando dos medias móviles:

- `HMA200`: Hull Moving Average de 200 periodos.
- `SMA200`: Simple Moving Average de 200 periodos.

Se plantean dos configuraciones simétricas:

### Entrada Long

La señal se considera **alcista** cuando se cumplen simultáneamente las siguientes cláusulas:

1. **Tendencia macro (4h)**: la `HMA200 (4H)` del último cierre válido queda por debajo del precio actual (close 5 m).
2. **Tendencia operativa (1h)**: la `HMA200 (1H)` cerrada queda por debajo del precio actual.
3. **Disparo (5m)**: el precio del timeframe 5M está por encima de la `SMA200 (5M)`.

Cuando las tres condiciones son verdaderas, el bot habilita una entrada en largo.

### Entrada Short

La versión bajista invierte las condiciones:

1. **Tendencia macro (4h)**: la `HMA200 (4H)` cerrada queda por encima del precio actual (close 5 m).
2. **Tendencia operativa (1h)**: la `HMA200 (1H)` cerrada queda por encima del precio actual.
3. **Disparo (5m)**: el precio del timeframe 5M está por debajo de la `SMA200 (5M)`.

Si las tres reglas son ciertas, el bot habilita una entrada en corto.

## Lógica de Evaluación

1. Se recopilan series de cierres (`close`) para los timeframes `5m`, `1h` y `4h`.
2. Se calculan las medias:
   - `SMA200` para `5m`.
   - `HMA200` de `1h` y `4h` utilizando únicamente velas cerradas.
3. Se compara el close actual de 5 m contra la SMA200 de 5 m y las HMA200 (1 h/4 h) más recientes cerradas.
4. El disparo final (`should_enter_long` o `should_enter_short`) es verdadero solo si las tres comparaciones resultan coherentes (mayores para long, menores para short).

## Referencia de código

Ubicación de la implementación:

- Indicadores: `apps/strategies/indicators.py`
- Evaluación de señales long/short: `apps/strategies/signals.py`

Ambos módulos están listos para reuso en backtesting y ejecución en vivo. La función principal es:

```python
from apps.strategies.signals import evaluate_long_signal, evaluate_short_signal

result = evaluate_long_signal({
    "5m": close_series_5m,
    "1h": close_series_1h,
    "4h": close_series_4h,
})

if result.should_enter:
    # lanzar orden long

short_result = evaluate_short_signal({
    "5m": close_series_5m,
    "1h": close_series_1h,
    "4h": close_series_4h,
})

if short_result.should_enter:
    # lanzar orden short
```

La estructura `SignalResult` incluye un desglose por timeframe para facilitar depuración y dashboards, y los atributos `direction` / `should_enter_long` / `should_enter_short` indican la orientación de la señal.

## Próximos pasos sugeridos

- Añadir condiciones de salida (take profit, trailing stop, etc.).
- Incluir una versión “short” invertida (precio debajo de HMA/SMA).
- Integrar filtros de volatilidad o momentum para reducir falsos positivos.
- Conectar esta evaluación con un motor de backtesting (Backtrader, vectorbt) para validar métricas.

## Visualización y Backtesting

Para replicar la experiencia combinando datos históricos, PnL y gráficas:

1. Obtener los datos de OHLCV multi-timeframe (por ejemplo con CCXT o APIs del exchange).
2. Evaluar las señales con `evaluate_long_signal` / `evaluate_short_signal`.
3. Registrar entradas y salidas en un DataFrame de operaciones (vectorbt/Backtrader simplifican el proceso).
4. Graficar velas e indicadores (`SMA200`, `HMA200`) con librerías como Plotly, Bokeh o mplfinance.
