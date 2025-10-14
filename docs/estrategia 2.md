entrada long
crossover sma200 5m vs hma200 4h. el ultimo punto de la sma200 5m cierra sobre el ultimo punto posible de calcular de la hma200 4h (tomando el criterio de la estrategia 1 para este calculo) y el punto anterior de la sma200 5m cerro por debajo de la hma200 4h. es decir, es un crossover hacia arriba de sma200 5m vs hma200 4h.

salida long
condicion 1: crossover sma200 5m vs hma200 1h. el ultimo punto de la sma200 5m cierra por debajo del ultimo punto posible de calcular de la hma200 1h (tomando el criterio de la estrategia 1 para este calculo) y el punto anterior de la sma200 5m cerro por sobre de la hma200 1h. es decir, es un crossover hacia abajo de sma200 5m vs hma200 1h.
condicion 2: crossover sma200 5m vs hma200 4h. crossover hacia abajo de sma200 5m vs hma200 4h (señal de entrada short, cierra el long).

entrada short
crossover sma200 5m vs hma200 4h. crossover hacia abajo de sma200 5m vs hma200 4h.

salida short
condicion 1: crossover sma200 5m vs hma200 1h. crossover hacia arriba de sma200 5m vs hma200 1h.
condicion 2: crossover sma200 5m vs hma200 4h. crossover hacia arriba de sma200 5m vs hma200 4h (señal de entrada long, cierra el short).

---

# Estrategia 2 - Crossover SMA/HMA 200

## 📖 Resumen

Esta estrategia se basa en **crossovers** (cruces) entre la SMA 200 de 5 minutos y las HMA 200 de diferentes timeframes. A diferencia de la Estrategia 1 que requiere alineación simultánea de múltiples condiciones, la Estrategia 2 genera señales específicamente cuando las medias móviles se cruzan.

### Componentes:
- **SMA200 (5m)**: Simple Moving Average de 200 períodos en timeframe de 5 minutos
- **HMA200 (1h)**: Hull Moving Average de 200 períodos en timeframe de 1 hora  
- **HMA200 (4h)**: Hull Moving Average de 200 períodos en timeframe de 4 horas

### Filosofía:
Los crossovers son momentos de cambio de tendencia potencial. La estrategia usa timeframes más largos (4h) para entradas y timeframes más cortos (1h) para salidas, permitiendo capturar tendencias importantes mientras se protege con salidas más tempranas.

---

## 🟢 Entrada Long (Compra)

### Condición de Entrada:
**Crossover alcista de SMA 200 (5m) sobre HMA 200 (4h)**

Se genera una señal de compra cuando:
1. En la vela **anterior** de 5m: `SMA 200 (5m) <= HMA 200 (4h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) > HMA 200 (4h)`

**Significado:**
- La media móvil de corto plazo (5m) cruza hacia arriba la media de largo plazo (4h)
- Indica el inicio potencial de una tendencia alcista
- Confirma momentum alcista sostenido

**Ejemplo visual:**
```
Tiempo    SMA(5m)   HMA(4h)   Estado
-------------------------------------
T-1       49,800    50,000    SMA debajo → No señal
T0        50,100    50,000    SMA arriba → ✅ ENTRADA LONG
```

---

## 🔴 Entrada Short (Venta en corto)

### Condición de Entrada:
**Crossover bajista de SMA 200 (5m) bajo HMA 200 (4h)**

Se genera una señal de venta cuando:
1. En la vela **anterior** de 5m: `SMA 200 (5m) >= HMA 200 (4h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) < HMA 200 (4h)`

**Significado:**
- La media móvil de corto plazo (5m) cruza hacia abajo la media de largo plazo (4h)
- Indica el inicio potencial de una tendencia bajista
- Confirma momentum bajista sostenido

**Ejemplo visual:**
```
Tiempo    SMA(5m)   HMA(4h)   Estado
-------------------------------------
T-1       50,200    50,000    SMA arriba → No señal
T0        49,900    50,000    SMA debajo → ✅ ENTRADA SHORT
```

---

## 🚪 Salida de Posiciones

### Cierre de Posición LONG

Una posición LONG se cierra cuando se cumple **CUALQUIERA** de estas dos condiciones:

#### Condición 1: Crossover bajista vs HMA 1h (Salida temprana)
**Crossover bajista de SMA 200 (5m) bajo HMA 200 (1h)**

1. En la vela **anterior** de 5m: `SMA 200 (5m) >= HMA 200 (1h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) < HMA 200 (1h)`

**¿Por qué HMA 1h para salidas tempranas?**
- Permite salir más temprano que la entrada (4h)
- Protege ganancias sin esperar una reversión completa
- Balance entre evitar salidas prematuras y proteger capital

#### Condición 2: Crossover bajista vs HMA 4h (Señal de SHORT)
**Crossover bajista de SMA 200 (5m) bajo HMA 200 (4h)**

1. En la vela **anterior** de 5m: `SMA 200 (5m) >= HMA 200 (4h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) < HMA 200 (4h)`

**Significado:**
- Es una señal de entrada SHORT
- Indica reversión fuerte de la tendencia
- Cierra el LONG y permite abrir SHORT inmediatamente

**Ejemplo completo:**
```
Posición LONG abierta en 50,000

Escenario A - Salida por HMA 1h:
Tiempo    SMA(5m)   HMA(1h)   HMA(4h)   Acción
--------------------------------------------------
T-1       50,300    50,000    49,500    Mantener
T0        49,900    50,000    49,500    ✅ CERRAR (1h)

Escenario B - Salida por HMA 4h:
Tiempo    SMA(5m)   HMA(1h)   HMA(4h)   Acción
--------------------------------------------------
T-1       49,600    49,800    49,500    Mantener
T0        49,400    49,800    49,500    ✅ CERRAR (4h)
```

### Cierre de Posición SHORT

Una posición SHORT se cierra cuando se cumple **CUALQUIERA** de estas dos condiciones:

#### Condición 1: Crossover alcista vs HMA 1h (Salida temprana)
**Crossover alcista de SMA 200 (5m) sobre HMA 200 (1h)**

1. En la vela **anterior** de 5m: `SMA 200 (5m) <= HMA 200 (1h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) > HMA 200 (1h)`

#### Condición 2: Crossover alcista vs HMA 4h (Señal de LONG)
**Crossover alcista de SMA 200 (5m) sobre HMA 200 (4h)**

1. En la vela **anterior** de 5m: `SMA 200 (5m) <= HMA 200 (4h)`
2. En la vela **actual** de 5m: `SMA 200 (5m) > HMA 200 (4h)`

**Significado:**
- Es una señal de entrada LONG
- Indica reversión fuerte de la tendencia
- Cierra el SHORT y permite abrir LONG inmediatamente

**Ejemplo completo:**
```
Posición SHORT abierta en 50,000

Escenario A - Salida por HMA 1h:
Tiempo    SMA(5m)   HMA(1h)   HMA(4h)   Acción
--------------------------------------------------
T-1       49,700    50,000    50,500    Mantener
T0        50,100    50,000    50,500    ✅ CERRAR (1h)

Escenario B - Salida por HMA 4h:
Tiempo    SMA(5m)   HMA(1h)   HMA(4h)   Acción
--------------------------------------------------
T-1       50,400    50,200    50,500    Mantener
T0        50,600    50,200    50,500    ✅ CERRAR (4h)
```

---

## 🔍 Detalles Técnicos de Implementación

### Algoritmo de Detección de Crossover

Para cada vela de 5 minutos, el sistema:

1. **Calcula los indicadores**:
   - SMA 200 sobre el timeframe de 5m
   - HMA 200 sobre el timeframe de 1h
   - HMA 200 sobre el timeframe de 4h

2. **Sincronización temporal**:
   - Usa `merge_asof` (pandas) para alinear HMA de 1h y 4h con cada vela de 5m
   - Toma el valor más reciente disponible de cada HMA
   - Mantiene consistencia con la Estrategia 1

3. **Detección de crossover**:
   ```python
   # Entrada LONG
   crossover_long = (prev_sma <= prev_hma_4h) and (current_sma > current_hma_4h)
   
   # Salidas LONG (cualquiera de las dos)
   exit_long_1h = (prev_sma >= prev_hma_1h) and (current_sma < current_hma_1h)
   exit_long_4h = (prev_sma >= prev_hma_4h) and (current_sma < current_hma_4h)
   exit_long = position_long_open and (exit_long_1h or exit_long_4h)
   
   # Entrada SHORT
   crossover_short = (prev_sma >= prev_hma_4h) and (current_sma < current_hma_4h)
   
   # Salidas SHORT (cualquiera de las dos)
   exit_short_1h = (prev_sma <= prev_hma_1h) and (current_sma > current_hma_1h)
   exit_short_4h = (prev_sma <= prev_hma_4h) and (current_sma > current_hma_4h)
   exit_short = position_short_open and (exit_short_1h or exit_short_4h)
   ```

4. **Gestión de posiciones**:
   - Solo se abre una posición nueva si no hay ninguna abierta
   - No se permiten posiciones LONG y SHORT simultáneas
   - Las posiciones se mantienen hasta que se detecta el crossover de salida

### Variables de Estado

La estrategia mantiene:
- `position_long_open`: Boolean indicando si hay una posición LONG activa
- `position_short_open`: Boolean indicando si hay una posición SHORT activa
- `prev_sma`: Valor anterior de SMA 200 (5m)
- `prev_hma_1h`: Valor anterior de HMA 200 (1h)
- `prev_hma_4h`: Valor anterior de HMA 200 (4h)

---

## 📊 Comparación con Estrategia 1

| Aspecto | Estrategia 1 | Estrategia 2 |
|---------|--------------|--------------|
| **Tipo** | Alineación multi-timeframe | Crossover |
| **Entradas** | Precio sobre todas las medias | Crossover SMA 5m vs HMA 4h |
| **Salidas** | Open y close bajo SMA | Doble: HMA 1h (temprana) o HMA 4h (reversión) |
| **Frecuencia** | Más señales | Menos señales |
| **Selectividad** | Menos selectiva | Más selectiva |
| **Tendencias** | Sigue tendencias existentes | Detecta cambios de tendencia |

### Ventajas de la Estrategia 2:

1. **Detección de cambios de tendencia**: Captura el momento exacto del cruce
2. **Menor frecuencia de operaciones**: Genera menos señales pero potencialmente más significativas
3. **Doble criterio de salida**: 
   - Salida temprana con HMA 1h (protege ganancias)
   - Salida por reversión con HMA 4h (cierre rápido ante cambio de tendencia)
4. **Prevención de drawdowns**: Cierra posiciones cuando hay señal contraria fuerte (4h)
5. **Lógica clara**: Fácil de entender y validar visualmente

### Desventajas:

1. **Puede perder parte de la tendencia**: Entra después que la tendencia ya comenzó
2. **Sensible a whipsaws**: Puede generar señales falsas en mercados laterales
3. **Requiere datos históricos**: Necesita valores previos para detectar crossovers

---

## 💻 Ubicación del Código

### Backend:
- **Archivo**: `apps/strategies/views.py`
- **Método**: `_evaluate_entries_strategy2()`
- **Líneas**: ~307-447

### Frontend:
- **Selector de estrategia**: `frontend/src/App.tsx`
- **Dropdown**: Permite cambiar entre "Strategy 1" y "Strategy 2"

### Uso del API:

```bash
# Estrategia 2
GET /api/strategies/hma-sma/run/?symbol=BTCUSDT&timeframe=5m&limit=500&strategy=2

# Estrategia 1 (default)
GET /api/strategies/hma-sma/run/?symbol=BTCUSDT&timeframe=5m&limit=500&strategy=1
```

---

## 🎯 Casos de Uso Recomendados

### Cuándo usar Estrategia 2:

1. **Mercados con tendencias claras**: Los crossovers funcionan mejor cuando hay tendencias definidas
2. **Trading menos frecuente**: Si prefieres menos operaciones pero más significativas
3. **Detección de reversiones**: Cuando buscas capturar cambios de tendencia importantes
4. **Backtesting comparativo**: Para comparar resultados vs Estrategia 1

### Cuándo NO usar Estrategia 2:

1. **Mercados laterales**: Los crossovers pueden generar muchas señales falsas
2. **Alta volatilidad**: Puede entrar y salir demasiado rápido
3. **Tendencias muy fuertes**: Puede perderse gran parte del movimiento inicial

---

## 📈 Sugerencias de Optimización

### Filtros adicionales a considerar:

1. **Volumen**: Solo operar crossovers con volumen significativo
2. **Distancia mínima**: Requerir que el crossover supere un umbral mínimo (ej: 0.5%)
3. **Confirmación de velas**: Esperar 2-3 velas después del crossover
4. **Filtro de volatilidad**: Evitar operar en períodos de alta volatilidad (ATR alto)

### Parámetros ajustables:

1. **Períodos de las medias**: Probar 150, 200, 250
2. **Timeframes**: Experimentar con diferentes combinaciones (ej: 15m, 2h, 6h)
3. **Stop loss**: Añadir stops fijos en % o basados en ATR
4. **Take profit**: Implementar targets en niveles técnicos

---

## ⚠️ Limitaciones y Consideraciones

### Situaciones problemáticas:

**Whipsaw (sierra):**
```
Tiempo    SMA(5m)   HMA(4h)   Acción
-----------------------------------------
T0        50,100    50,000    LONG abierto
T1        49,900    50,000    LONG cerrado (si usa mismo TF)
T2        50,100    50,000    LONG abierto otra vez
→ Múltiples entradas/salidas con pérdida de fees
```

**Solución implementada:** Usar 1h para salidas y 4h para entradas reduce este problema.

**Crossovers lentos:**
- Las HMA reaccionan más rápido que SMA tradicionales
- Sin embargo, pueden "quedarse atrás" en movimientos muy rápidos
- El crossover puede ocurrir tarde en la tendencia

**Datos faltantes:**
- Si faltan datos de 1h o 4h, no se pueden detectar crossovers
- El sistema maneja esto ignorando señales cuando los datos son `None`

---

## 📝 Registro de Cambios

**Versión 1.1** - 14 Octubre 2025
- ✨ Agregado doble criterio de salida para mayor protección
  - Salida temprana: Crossover vs HMA 1h (protege ganancias)
  - Salida por reversión: Crossover vs HMA 4h (cierre ante señal contraria)
- 🛡️ Mejora en prevención de drawdowns al cerrar posiciones cuando hay señal de reversión fuerte

**Versión 1.0** - 14 Octubre 2025
- Implementación inicial de Estrategia 2
- Crossover SMA 5m vs HMA 4h para entradas
- Crossover SMA 5m vs HMA 1h para salidas
- Integración con frontend mediante dropdown
- Soporte para posiciones LONG y SHORT

---

**Última actualización**: 14 Octubre 2025  
**Versión**: 1.1  
**Estado**: Activa y lista para backtesting
