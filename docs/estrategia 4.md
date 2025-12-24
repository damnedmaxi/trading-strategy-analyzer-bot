nombre: crossover sma200 5m vs hma200 1h

# #################### bias long:

 - la sma200 5m actual esta sobre la hma200 D (diaria)

abrir long:
 - la hma200 1h esta debajo de la sma200 1h.
 - la sma200 5m cruza la hma200 1h hacia arriba.
 

salida long:
 - la sma200 5m cruza la hma200 1h hacia abajo.

# #################### bias short:

 - la sma200 5m actual esta debajo la hma200 D (diaria)

abrir short:
 - la hma200 1h esta sobre de la sma200 1h.
 - la sma200 5m cruza la hma200 1h hacia abajo.

 salida short:
 - la sma200 5m cruza la hma200 1h hacia arriba.

# ####################################################################################################################################################################################
# ####################################################################################################################################################################################
# #################################################################################################################################################################################### 

Implementación en la app (resumen técnico)

- Timeframes e indicadores utilizados:
  - 5m: SMA200 (para los cruces) y precio actual.
  - 1h: HMA200 y SMA200 (para filtro de relación HMA1h vs SMA1h).
  - 1d: HMA200 (para bias diario).

- Reglas codificadas (idénticas a tus notas):
  - Bias long: SMA200(5m) > HMA200(1d)
    - Entrada long: HMA200(1h) < SMA200(1h) y SMA200(5m) cruza de abajo hacia arriba HMA200(1h).
    - Salida long: SMA200(5m) cruza de arriba hacia abajo HMA200(1h).
  - Bias short: SMA200(5m) < HMA200(1d)
    - Entrada short: HMA200(1h) > SMA200(1h) y SMA200(5m) cruza de arriba hacia abajo HMA200(1h).
    - Salida short: SMA200(5m) cruza de abajo hacia arriba HMA200(1h).

- Detalles de implementación:
  - Endpoint: `/api/strategies/hma-sma/run/?strategy=4`.
  - La fusión de timeframes usa `merge_asof` para mapear 1h/1d sobre marcas de tiempo de 5m (tolerancias 6h para 1h, 5d para 1d).
  - La detección de cruce se hace comparando valores previos vs actuales de SMA200(5m) y HMA200(1h).
  - La vista alinea las señales al timeframe seleccionado en el front para el gráfico y la tabla.

Posibles motivos de “sin señales” en el front end (y cómo verificar)

- Falta o insuficiente historia en 1d para HMA200:
  - Si no existen al menos ~200 velas diarias (1d), HMA200(1d) será `NaN` y el bias quedará indefinido (no habrá ni bias long ni short). Resultado: 0 señales.
  - Verifica en DB que haya velas `1d` para el símbolo y con suficiente historia. Si no, utiliza el script `apps/datafeeds/scripts/fetch_multi_timeframes.py` incluyendo `1d` y rango amplio de fechas.

- Falta o insuficiente historia en 1h para SMA200/HMA200:
  - Con menos de 200 velas 1h, alguno de los indicadores será `NaN` y no se activarán condiciones.
  - Recomendado: asegurar >200 velas 1h (ideal: varios miles) para pruebas robustas.

- Descalce temporal (merge) o tolerancias:
  - El merge asof usa `backward` con tolerancias (6h para 1h y 5d para 1d). Si no hay velas recientes dentro de la tolerancia, el indicador queda `NaN` en esa vela de 5m.
  - Asegúrate de haber descargado datos hasta la fecha actual para 1h y 1d.

- Requisitos de cruce estrictos:
  - El cruce exige que el valor previo esté al otro lado del HMA200(1h) y el actual lo haya cruzado. Si seleccionas un período corto sin ocurrencias de cruce, no verás señales.
  - Prueba expandir el rango (más `limit` o fechas más largas) para encontrar eventos.

- Colisiones de nombres de columnas por merges:
  - Si al fusionar se generan sufijos (`sma200_x`, `sma200_y`), la estrategia podría fallar o no evaluar bien.
  - Se añadió una normalización post-merge para garantizar que la SMA200(5m) se mantenga en `sma200` y la SMA200(1h) quede en `sma200_1h`.

Cómo cargar datos suficientes (ejemplo rápido)

```
python apps/datafeeds/scripts/fetch_multi_timeframes.py \
  BTCUSDT --base BTC --quote USDT \
  --timeframes 5m 1h 4h 1d \
  --start 2022-01-01 --end 2025-11-01 \
  --limit 1000 --exchange binance
```

Luego recarga la página del front y ejecuta la estrategia 4 con timeframe `5m` y un `limit` alto para observar cruces y señales.

Notas sobre visualización

- Por simplicidad, el chart muestra por defecto SMA200(5m) y HMA200 en 1h/4h. Si necesitas ver también HMA200(1d) y/o SMA200(1h) como overlays para depurar, puedo activarlos en la configuración del front/back.

Gestión de riesgo global (stop loss / take profit)

- La estrategia 4 ahora respeta las banderas globales `STOP_LOSS_ENABLED`, `STOP_LOSS_PERCENT`, `TAKE_PROFIT_ENABLED` y `TAKE_PROFIT_PERCENT` definidas en `apps/strategies/config.py`.
- Cuando están activadas, al abrir una posición se registran niveles de stop/take en base al precio de entrada y se generan las salidas correspondientes si se alcanzan durante la reproducción.
