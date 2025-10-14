# Diagnóstico y Correcciones del Frontend

## 🔴 Problemas Identificados y Corregidos

### 1. **Flechas Invisibles - Uso Incorrecto de Timestamps**

**Problema:**
- Los markers (flechas) estaban usando `entry.time` en lugar de `entry.sourceTime`
- `entry.time` = timestamp de la vela del timeframe de visualización (ej: 10:00 para 1h)
- `entry.sourceTime` = timestamp real cuando ocurrió la señal (ej: 10:15 en el timeframe base de 5m)
- Cuando el timeframe de visualización era > 5m, las flechas intentaban renderizarse en timestamps inexistentes

**Archivo:** `frontend/src/components/CandlestickChart.tsx` líneas 196-239

**Solución Aplicada:**
```typescript
// ANTES (❌):
case 'long':
  return {
    time: entry.time,  // timestamp de la vela de visualización
    position: 'belowBar',
    ...
  };

// DESPUÉS (✅):
case 'long':
  return {
    time: entry.sourceTime,  // timestamp real de la señal
    position: 'belowBar',
    ...
  };
```

### 2. **Markers Sin Puntos de Datos Subyacentes**

**Problema:**
- `markerSeries` (la serie invisible usada para anclar markers) solo tenía puntos de datos para los timestamps de las velas del timeframe de visualización
- Los markers intentaban aparecer en `sourceTime` (timestamps del timeframe base 5m)
- lightweight-charts no puede renderizar markers en timestamps sin puntos de datos subyacentes

**Archivo:** `frontend/src/components/CandlestickChart.tsx` líneas 148-154

**Solución Aplicada:**
- Crear puntos de datos en `markerSeries` para CADA `sourceTime` de las entradas visibles
- Interpolar precios para esos timestamps usando `entry.price` o la vela más cercana

```typescript
// Ahora markerSeries incluye:
// 1. Todos los timestamps de velas visibles
// 2. Todos los sourceTimes de las entradas (con precios interpolados)
```

### 3. **Desincronización Temporal en Filtrado de Entradas**

**Problema:**
- `cutoffTime` usaba `currentCandle.time` (inicio de la vela)
- Entradas con `sourceTime` dentro de la vela actual pero después de su inicio no se incluían
- Ejemplo: Vela 1h de 10:00-11:00, entrada a las 10:45 → NO visible porque 10:45 > 10:00

**Archivo:** `frontend/src/App.tsx` líneas 92-96

**Solución Aplicada:**
- Usar el timestamp de la **siguiente vela** como límite (o calcular el fin de la vela actual)
- Esto incluye todas las entradas que ocurren dentro del rango temporal de la vela actual

```typescript
// ANTES (❌):
const cutoffTime = currentCandle?.time ?? null;

// DESPUÉS (✅):
const cutoffTime = useMemo(() => {
  if (!currentCandle) return null;
  const nextCandle = candles[index + 1];
  if (nextCandle) {
    return nextCandle.time;
  }
  // Para la última vela, calcular el fin basado en timeframe
  const duration = timeframeDurations[effectiveTimeframe] || 5 * 60;
  return (currentCandle.time + duration) as UTCTimestamp;
}, [currentCandle, candles, index, effectiveTimeframe]);
```

---

## ✅ Resultados Esperados

Después de estas correcciones:

1. **Las flechas deben ser visibles** en todos los timeframes
2. **Las órdenes se cierran correctamente** en la UI cuando ocurre un exit
3. **El PnL se sincroniza** correctamente con las flechas mostradas
4. **Las métricas reflejan el estado real** de las posiciones en cada momento

---

## 🔧 Mejoras Adicionales Sugeridas

### 1. **Validación de Consistencia de Datos**

**Propósito:** Detectar y alertar sobre estados inconsistentes (ej: long_exit sin long previo)

```typescript
// En App.tsx, dentro del cálculo de metrics:
if (entry.direction === 'long_exit' && openLongPrice == null) {
  console.warn(`Long exit at ${entry.sourceTime} without open long position`);
}
```

### 2. **Visualización de Estado de Debug**

**Propósito:** Panel de debug para ayudar a diagnosticar problemas

```typescript
// Agregar un panel opcional que muestre:
- Número de entradas totales vs visibles
- Timestamp de cutoffTime actual
- Estado de posiciones abiertas
- Diferencia entre entry.time y entry.sourceTime para cada entrada
```

### 3. **Optimización de Rendimiento**

**Propósito:** Mejorar performance con muchas velas

```typescript
// En CandlestickChart.tsx, usar búsqueda binaria para encontrar vela más cercana
// En lugar de iterar linealmente sobre todas las velas
function findClosestCandle(candles: Candle[], targetTime: UTCTimestamp): Candle {
  // Implementar búsqueda binaria
}
```

### 4. **Manejo de Timeframe Dinámico**

**Propósito:** Advertir cuando las entradas son muy espaciadas para el timeframe

```typescript
// Detectar cuando sourceTime está muy lejos de cualquier vela visible
const maxAcceptableGap = timeframeDurations[effectiveTimeframe] * 2;
if (minDiff > maxAcceptableGap) {
  console.warn(`Entry at ${entry.sourceTime} is too far from any candle`);
}
```

### 5. **Tests Unitarios**

**Propósito:** Prevenir regresiones futuras

```typescript
describe('Entry filtering', () => {
  it('should include entries within current candle timeframe', () => {
    // Test que 10:45 se incluye cuando currentCandle es 10:00-11:00
  });
  
  it('should use sourceTime for markers', () => {
    // Test que markers usan sourceTime no time
  });
});
```

### 6. **Tooltip Mejorado para Markers**

**Propósito:** Mostrar más información al hacer hover sobre las flechas

```typescript
// Agregar información detallada en el texto del marker:
text: `LONG @ ${entry.price?.toFixed(2)} (${formatTime(entry.sourceTime)})`
```

### 7. **Visualización de Rangos Temporales**

**Propósito:** Ayudar a entender la diferencia entre time y sourceTime

```typescript
// Agregar líneas verticales semi-transparentes para mostrar
// el rango de tiempo de cada vela del timeframe de visualización
```

---

## 📊 Diferencia entre `time` y `sourceTime`

### Conceptos Clave

**Backend (`apps/strategies/views.py`):**
- La estrategia se ejecuta en el timeframe **base** (5m)
- Cada señal se genera en un timestamp específico de 5m
- Al alinear para visualización, se mapea a la vela del timeframe solicitado

**`source_time` (timestamp real):**
- El momento exacto en el timeframe base (5m) cuando ocurrió la señal
- Ejemplo: `2024-01-15T10:15:00Z`

**`time` (timestamp alineado):**
- El inicio de la vela del timeframe de visualización que contiene esa señal
- Ejemplo para 1h: `2024-01-15T10:00:00Z`

### Ejemplo Práctico

```
Timeframe de visualización: 1h
Señal real: 10:15 (en timeframe base de 5m)

Backend genera:
{
  "time": "2024-01-15T10:00:00Z",      // inicio de vela de 1h
  "source_time": "2024-01-15T10:15:00Z", // momento real de la señal
  "direction": "long",
  "price": 50000.0
}

Frontend debe:
✅ Mostrar marker en sourceTime (10:15) - donde realmente ocurrió
✅ Filtrar por sourceTime para sincronización correcta
✅ Crear datos en markerSeries para sourceTime
```

---

## 🧪 Pruebas Recomendadas

1. **Timeframe 5m:**
   - Verificar que las flechas aparecen correctamente
   - `time` y `sourceTime` deberían ser iguales

2. **Timeframe 1h:**
   - Verificar que las flechas aparecen en momentos intermedios de las velas
   - Las órdenes deben cerrarse cuando aparece la flecha de exit

3. **Timeframe 4h:**
   - Caso más extremo de diferencia temporal
   - Múltiples señales pueden aparecer dentro de una sola vela

4. **Playback:**
   - Avanzar vela por vela y verificar que las órdenes abren/cierran correctamente
   - El PnL debe actualizarse en tiempo real

5. **Edge Cases:**
   - Última vela del dataset
   - Primera vela después de resetear
   - Cambio de timeframe con playback activo

---

## 📝 Archivos Modificados

1. **`frontend/src/components/CandlestickChart.tsx`:**
   - Líneas 196-239: Cambio de `entry.time` a `entry.sourceTime` en markers
   - Líneas 152-193: Nueva lógica para poblar markerSeries con sourceTimes

2. **`frontend/src/App.tsx`:**
   - Líneas 92-110: Nueva lógica para calcular cutoffTime correctamente

---

## 🎯 Conclusión

Los tres problemas principales estaban relacionados con el manejo inconsistente de timestamps:
- **Markers** usaban el campo incorrecto
- **MarkerSeries** no tenía datos para los timestamps correctos
- **Filtrado** no incluía entradas dentro de la vela actual

Con estas correcciones, el frontend debería sincronizar correctamente las órdenes y mostrar todas las flechas de entrada/salida en los momentos precisos.

