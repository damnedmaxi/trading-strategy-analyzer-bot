# Estrategia SMA/HMA 200 – Guía Completa

## 📖 Resumen

Esta estrategia combina múltiples timeframes para confirmar tendencias y generar señales de trading precisas. Utiliza dos tipos de medias móviles:

- **HMA200**: Hull Moving Average de 200 períodos (más reactiva a cambios de tendencia)
- **SMA200**: Simple Moving Average de 200 períodos (más suave y tradicional)

La estrategia se basa en el concepto de **confluencia**: una señal solo es válida cuando TODAS las condiciones se cumplen simultáneamente en los diferentes timeframes.

---

## 🟢 Entrada Long (Compra)

Una señal de **compra (LONG)** se genera cuando el precio cumple **TODAS** estas condiciones al mismo tiempo:

### 1. 📊 Tendencia Macro (4h) - Confirmación de largo plazo
**El precio actual (cierre de 5m) debe estar POR ENCIMA de la `HMA200 (4h)` más reciente**

- Se toma el valor más reciente disponible de la HMA calculada en velas de 4 horas
- Esto confirma que la tendencia de largo plazo es alcista
- Filtra operaciones contra la tendencia principal

### 2. 📈 Tendencia Operativa (1h) - Confirmación de mediano plazo  
**El precio actual (cierre de 5m) debe estar POR ENCIMA de la `HMA200 (1h)` más reciente**

- Se toma el valor más reciente disponible de la HMA calculada en velas de 1 hora
- Esto confirma que la tendencia de mediano plazo también es alcista
- Añade una capa adicional de confirmación antes del disparo

### 3. 🎯 Disparo (5m) - Señal de entrada inmediata
**El precio actual (cierre de 5m) debe estar POR ENCIMA de la `SMA200 (5m)`**

- Este es el "gatillo" que dispara la entrada
- Cuando el precio de corto plazo también supera su media móvil, todas las tendencias están alineadas
- Momento óptimo para entrar con alta probabilidad de éxito

✅ **Resultado:** Cuando las **TRES** condiciones son verdaderas, el bot abre una posición LONG (compra).

**Ejemplo visual:**
```
Precio 5m:     50,500  ↑
              --------
SMA 200 (5m):  50,000  ✓ Precio arriba
HMA 200 (1h):  49,800  ✓ Precio arriba
HMA 200 (4h):  49,500  ✓ Precio arriba

→ ✅ Todas las condiciones OK → ABRIR LONG
```

---

## 🔴 Entrada Short (Venta en corto)

Una señal de **venta en corto (SHORT)** se genera cuando el precio cumple **TODAS** estas condiciones al mismo tiempo:

### 1. 📊 Tendencia Macro (4h) - Confirmación de largo plazo
**El precio actual (cierre de 5m) debe estar POR DEBAJO de la `HMA200 (4h)` más reciente**

- Se toma el valor más reciente disponible de la HMA calculada en velas de 4 horas
- Esto confirma que la tendencia de largo plazo es bajista
- Filtra operaciones contra la tendencia principal

### 2. 📉 Tendencia Operativa (1h) - Confirmación de mediano plazo
**El precio actual (cierre de 5m) debe estar POR DEBAJO de la `HMA200 (1h)` más reciente**

- Se toma el valor más reciente disponible de la HMA calculada en velas de 1 hora
- Esto confirma que la tendencia de mediano plazo también es bajista
- Añade una capa adicional de confirmación antes del disparo

### 3. 🎯 Disparo (5m) - Señal de entrada inmediata
**El precio actual (cierre de 5m) debe estar POR DEBAJO de la `SMA200 (5m)`**

- Este es el "gatillo" que dispara la entrada
- Cuando el precio de corto plazo también está bajo su media móvil, todas las tendencias están alineadas
- Momento óptimo para entrar con alta probabilidad de éxito

✅ **Resultado:** Cuando las **TRES** condiciones son verdaderas, el bot abre una posición SHORT (venta).

**Ejemplo visual:**
```
HMA 200 (4h):  49,500  ✓ Precio debajo
HMA 200 (1h):  49,800  ✓ Precio debajo
SMA 200 (5m):  50,000  ✓ Precio debajo
              --------
Precio 5m:     48,500  ↓

→ ✅ Todas las condiciones OK → ABRIR SHORT
```

---

## 🚪 Salida de Posiciones

### Cierre de Posición LONG

Una posición LONG se cierra cuando una vela de 5 minutos cumple **AMBAS** condiciones:

1. **Apertura (open) de la vela está POR DEBAJO de la SMA200 (5m)**
2. **Cierre (close) de la vela está POR DEBAJO de la SMA200 (5m)**

**¿Por qué ambas condiciones?**  
Para evitar salidas prematuras por volatilidad intra-vela. Solo cerramos cuando la vela completa confirma el cruce a la baja.

**Ejemplo de CIERRE:**
```
Vela 1: Open=50,100, Close=49,900, SMA=50,000
        → Open arriba, Close abajo → NO CIERRA (falta confirmación)

Vela 2: Open=49,800, Close=49,700, SMA=50,000
        → Open abajo, Close abajo → ✅ CIERRA (confirmado)
```

### Cierre de Posición SHORT

Una posición SHORT se cierra cuando una vela de 5 minutos cumple **AMBAS** condiciones:

1. **Apertura (open) de la vela está POR ENCIMA de la SMA200 (5m)**
2. **Cierre (close) de la vela está POR ENCIMA de la SMA200 (5m)**

**Ejemplo de CIERRE:**
```
Vela 1: Open=49,900, Close=50,100, SMA=50,000
        → Open abajo, Close arriba → NO CIERRA (falta confirmación)

Vela 2: Open=50,200, Close=50,300, SMA=50,000
        → Open arriba, Close arriba → ✅ CIERRA (confirmado)
```

---

## 🔍 Lógica de Evaluación (Técnica)

Para desarrolladores y traders avanzados:

1. **Recopilación de datos**: Se obtienen series de cierres (`close`) para los timeframes `5m`, `1h` y `4h`

2. **Cálculo de indicadores**:
   - `SMA200` se calcula sobre las velas de `5m`
   - `HMA200` se calcula sobre las velas de `1h` y `4h` por separado

3. **Sincronización temporal**: 
   - Se usa `merge_asof` (pandas) para alinear los valores de HMA de 1h y 4h con cada vela de 5m
   - Esto permite comparar el precio actual de 5m con los indicadores de timeframes mayores

4. **Evaluación**:
   - Para cada vela de 5m, se compara su precio de cierre con:
     - SMA200 de la misma vela (5m)
     - HMA200 más reciente disponible de 1h
     - HMA200 más reciente disponible de 4h

5. **Generación de señales**:
   - `should_enter_long` = `(precio > SMA_5m) AND (precio > HMA_1h) AND (precio > HMA_4h)`
   - `should_enter_short` = `(precio < SMA_5m) AND (precio < HMA_1h) AND (precio < HMA_4h)`

6. **Gestión de posiciones**:
   - Solo se abre una posición nueva si no hay ninguna abierta
   - Las posiciones se mantienen hasta que se cumplen las condiciones de salida
   - No se permiten posiciones LONG y SHORT simultáneas

---

## 💻 Referencia de Código

### Ubicación de la implementación:

- **Indicadores**: `apps/strategies/indicators.py`
- **Evaluación de señales**: `apps/strategies/signals.py`
- **Lógica de entrada/salida**: `apps/strategies/views.py` (método `_evaluate_entries`)

### Ejemplo de uso (API de señales):

```python
from apps.strategies.signals import evaluate_long_signal, evaluate_short_signal

# Preparar series de datos
closes_by_timeframe = {
    "5m": close_series_5m,   # Serie pandas con precios de cierre de 5m
    "1h": close_series_1h,   # Serie pandas con precios de cierre de 1h
    "4h": close_series_4h,   # Serie pandas con precios de cierre de 4h
}

# Evaluar señal LONG
result = evaluate_long_signal(closes_by_timeframe)

if result.should_enter:
    print(f"✅ Señal LONG detectada")
    print(f"Breakdown por timeframe:")
    for tf, breakdown in result.breakdown.items():
        print(f"  {tf}: Precio={breakdown.price}, "
              f"Indicador={breakdown.indicator_value}, "
              f"Cumple={breakdown.condition_met}")

# Evaluar señal SHORT
short_result = evaluate_short_signal(closes_by_timeframe)

if short_result.should_enter:
    print(f"✅ Señal SHORT detectada")
```

### Estructura de `SignalResult`:

```python
@dataclass
class SignalResult:
    should_enter: bool              # ¿Se debe entrar?
    breakdown: dict                 # Desglose por timeframe para debugging
    direction: Optional[str]        # "long" o "short" o None
```

---

## 🎯 Ventajas de esta Estrategia

1. **Confluencia Multi-Timeframe**: Requiere alineación de todas las tendencias, reduciendo falsos positivos

2. **Adaptativa**: La HMA reacciona más rápido que una SMA tradicional, capturando cambios de tendencia antes

3. **Clara Jerarquía**: 
   - 4h = Dirección general (¿alcista o bajista?)
   - 1h = Confirmación de momentum
   - 5m = Timing de entrada preciso

4. **Salidas Confirmadas**: Al requerir que open Y close crucen la SMA, se evitan salidas por ruido intra-vela

5. **Backtesteable**: Toda la lógica es determinista y puede validarse con datos históricos

---

## ⚠️ Consideraciones y Limitaciones

### Situaciones donde NO se genera señal:

- **Mercado lateral**: Si el precio oscila alrededor de las medias sin tendencia clara
- **Divergencia de timeframes**: Si 4h es alcista pero 1h es bajista (o viceversa)
- **Volatilidad extrema**: Las HMA pueden "quedarse atrás" en movimientos muy rápidos

### Casos especiales de salida:

**Caso A: Precio oscila en la SMA**
```
Vela 1: Open=49,900, Close=50,100, SMA=50,000
        → No se cierra (close arriba de SMA)

Vela 2: Open=50,100, Close=49,900, SMA=50,000
        → No se cierra (open arriba de SMA)

Vela 3: Open=49,800, Close=49,700, SMA=50,000
        → ✅ Se cierra (ambos abajo)
```

La posición puede mantenerse varias velas mientras el precio "baila" alrededor de la SMA.

**Caso B: Spike repentino**
```
Posición LONG abierta en 50,000
Precio cae a 48,000 (drawdown del 4%)
Pero nunca hay una vela con open Y close abajo de SMA
→ La posición NO se cierra automáticamente
```

Esto puede llevar a drawdowns mayores que en estrategias con stop-loss fijo.

---

## 🚀 Próximos Pasos Sugeridos

### Mejoras de la Estrategia:

1. **Stop Loss y Take Profit**:
   - Añadir stops fijos (ej: 2% de pérdida máxima)
   - Implementar trailing stop para proteger ganancias
   - Take profit en niveles de soporte/resistencia

2. **Filtros Adicionales**:
   - Volumen: Solo entrar si hay volumen suficiente
   - Volatilidad: Evitar entradas en mercados muy volátiles (ATR alto)
   - Horarios: Filtrar horarios de baja liquidez

3. **Optimización de Parámetros**:
   - Probar diferentes períodos (¿150? ¿250?)
   - Evaluar otros timeframes (¿30m en vez de 1h?)
   - Backtesting exhaustivo para encontrar configuración óptima

### Infraestructura:

1. **Testing Automatizado**:
   - Unit tests para cada condición
   - Integration tests del flujo completo
   - Backtests con datos históricos extensos

2. **Monitoreo**:
   - Alertas cuando se genera una señal
   - Dashboard con estado actual de todas las condiciones
   - Logs detallados de todas las decisiones

3. **Ejecución en Vivo**:
   - Conectar con exchange real (paper trading primero)
   - Sistema de gestión de riesgo
   - Alerts por Telegram/Email cuando hay señales

---

## 📊 Visualización y Backtesting

### Pasos para validar la estrategia:

1. **Obtener datos históricos**: Descargar OHLCV de múltiples timeframes (CCXT, exchange APIs)

2. **Ejecutar la estrategia**: Usar el endpoint `/api/strategies/hma-sma/run/` o el código Python directamente

3. **Analizar resultados**:
   - Win rate (% de trades ganadores)
   - Profit factor (ganancias totales / pérdidas totales)
   - Maximum drawdown (máxima caída desde peak)
   - Sharpe ratio (retorno ajustado por riesgo)

4. **Visualizar**:
   - Gráfico de velas con SMA y HMA superpuestas
   - Markers en puntos de entrada/salida
   - Curva de equity (evolución del capital)

### Herramientas recomendadas:

- **Frontend actual**: Ya integrado en `http://localhost:5173`
- **Backtrader**: Framework Python completo para backtesting
- **vectorbt**: Backtesting vectorizado (muy rápido)
- **TradingView**: Para análisis visual y compartir ideas

---

## 📝 Glosario

- **HMA (Hull Moving Average)**: Media móvil que reduce el lag usando weighted moving averages anidadas
- **SMA (Simple Moving Average)**: Media aritmética simple de los últimos N precios
- **Confluencia**: Alineación de múltiples indicadores o timeframes apuntando en la misma dirección
- **Timeframe**: Intervalo de tiempo de cada vela (5m = 5 minutos, 1h = 1 hora, etc.)
- **Long**: Posición de compra (se gana si el precio sube)
- **Short**: Posición de venta (se gana si el precio baja)
- **Drawdown**: Caída porcentual desde un máximo histórico
- **Backtesting**: Simulación de la estrategia con datos históricos

---

**Última actualización**: 13 Octubre 2025  
**Versión de la estrategia**: 1.1 (con corrección de bug de estado de posiciones)
