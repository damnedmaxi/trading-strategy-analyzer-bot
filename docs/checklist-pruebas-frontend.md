# ✅ Checklist de Pruebas - Correcciones Frontend

## 🎯 Objetivo
Verificar que las correcciones implementadas resuelvan los problemas de:
- Flechas invisibles
- Órdenes que no se cierran
- Desincronización de PnL

---

## 🧪 Pruebas a Realizar

### 1. **Prueba Básica - Timeframe 5m**

**Objetivo:** Verificar que las flechas aparecen en el timeframe base

- [ ] Abrir http://localhost:5173
- [ ] Seleccionar símbolo: **BTCUSDT**
- [ ] Seleccionar timeframe: **5m**
- [ ] Cargar datos (botón "Reload data")
- [ ] **Verificar:** ¿Aparecen flechas de colores en el gráfico?
  - 🟢 Verde (↑) = LONG entry
  - 🔴 Rojo (↓) = SHORT entry
  - 🟠 Naranja (↓) = LONG EXIT
  - 🔵 Azul (↑) = SHORT EXIT

**Resultado esperado:** ✅ Las flechas deben ser visibles

---

### 2. **Prueba Crítica - Timeframe 1h**

**Objetivo:** Verificar que las flechas aparecen en timeframes mayores

- [ ] Cambiar timeframe a: **1h**
- [ ] Esperar a que cargue
- [ ] **Verificar:** ¿Las flechas siguen siendo visibles?
- [ ] **Verificar:** ¿Las flechas aparecen en posiciones intermedias dentro de las velas de 1h?

**Resultado esperado:** ✅ Las flechas deben aparecer en momentos específicos dentro de las velas horarias

---

### 3. **Prueba de Sincronización - Playback**

**Objetivo:** Verificar que las órdenes se abren y cierran correctamente

- [ ] Ir al inicio del playback (botón ⏮)
- [ ] Observar el panel de "Position:" que muestra "FLAT"
- [ ] Avanzar paso a paso (▶) hasta encontrar una flecha verde (LONG)
- [ ] **Verificar:** ¿El panel de "Position:" cambia a "LONG @ [precio]"?
- [ ] **Verificar:** ¿El "Open PnL" empieza a cambiar?
- [ ] Continuar avanzando hasta encontrar una flecha naranja (LONG EXIT)
- [ ] **Verificar:** ¿El panel de "Position:" vuelve a "FLAT"?
- [ ] **Verificar:** ¿El "Closed PnL" se actualizó?
- [ ] **Verificar:** ¿El "Open PnL" volvió a 0?

**Resultado esperado:** ✅ Las posiciones deben abrirse y cerrarse exactamente cuando aparecen las flechas

---

### 4. **Prueba Extrema - Timeframe 4h**

**Objetivo:** Verificar el caso más extremo de diferencia temporal

- [ ] Cambiar timeframe a: **4h**
- [ ] **Verificar:** ¿Las flechas siguen siendo visibles?
- [ ] **Observar:** Puede haber múltiples flechas dentro de una sola vela de 4h
- [ ] Usar playback para avanzar vela por vela
- [ ] **Verificar:** ¿Las órdenes se sincronizan correctamente?

**Resultado esperado:** ✅ Incluso con velas de 4h, las señales deben aparecer en los momentos correctos

---

### 5. **Prueba de Consistencia - Contador de Trades**

**Objetivo:** Verificar que el conteo de trades sea consistente

- [ ] Seleccionar timeframe: **5m**
- [ ] Ir al final del playback (botón ⏭)
- [ ] Anotar el número de "Trades:" del panel
- [ ] Cambiar timeframe a: **1h**
- [ ] Esperar que cargue
- [ ] Ir al final del playback (botón ⏭)
- [ ] **Verificar:** ¿El número de "Trades:" es el mismo?

**Resultado esperado:** ✅ El número de trades debe ser idéntico independientemente del timeframe

---

### 6. **Prueba Visual - Flechas en el Gráfico**

**Objetivo:** Verificar que todas las flechas sean visibles y distinguibles

- [ ] Seleccionar timeframe: **30m**
- [ ] Hacer zoom en una sección con varias señales
- [ ] **Verificar colores:**
  - 🟢 LONG = Verde, flecha hacia arriba, debajo de la vela
  - 🔴 SHORT = Rojo, flecha hacia abajo, encima de la vela
  - 🟠 LONG EXIT = Naranja, flecha hacia abajo, encima de la vela
  - 🔵 SHORT EXIT = Azul, flecha hacia arriba, debajo de la vela
- [ ] **Verificar:** ¿Las flechas están alineadas con el precio correcto?

**Resultado esperado:** ✅ Todas las flechas deben ser claramente visibles y estar en las posiciones correctas

---

### 7. **Prueba de PnL - Cálculo Correcto**

**Objetivo:** Verificar que el PnL se calcula correctamente

- [ ] Seleccionar timeframe: **1h**
- [ ] Configurar "Position Size": **10000** USD
- [ ] Ir al inicio (⏮)
- [ ] Reproducir en automático (Play)
- [ ] **Observar durante la reproducción:**
  - [ ] ¿El "Open PnL" cambia mientras hay una posición abierta?
  - [ ] ¿El "Closed PnL" se actualiza solo cuando se cierra una posición?
  - [ ] ¿El "Total PnL" = Closed + Open?
- [ ] Pausar en una posición LONG abierta
- [ ] **Verificar:** Si el precio sube, ¿el Open PnL es positivo?
- [ ] **Verificar:** Si el precio baja, ¿el Open PnL es negativo?

**Resultado esperado:** ✅ El PnL debe reflejar las ganancias/pérdidas correctamente

---

## 🐛 Problemas Anteriores vs Ahora

### Antes de las Correcciones ❌

```
Problema 1: Flechas invisibles
- En timeframe 1h → NO se veían flechas
- En timeframe 4h → NO se veían flechas
- Solo funcionaba en 5m

Problema 2: Órdenes no se cerraban
- Una posición LONG se abría
- La flecha de LONG EXIT aparecía (o debería aparecer)
- La posición seguía mostrando "LONG @ [precio]"
- El Open PnL nunca se cerraba

Problema 3: PnL desincronizado
- El contador de trades no coincidía con las flechas visibles
- El Closed PnL no se actualizaba correctamente
```

### Después de las Correcciones ✅

```
Solución 1: Flechas visibles en todos los timeframes
- Uso de sourceTime en lugar de time
- Datos en markerSeries para cada sourceTime
- Flechas aparecen exactamente cuando ocurrieron las señales

Solución 2: Órdenes se cierran correctamente
- Filtrado temporal ajustado para incluir entradas dentro de la vela actual
- cutoffTime usa el inicio de la siguiente vela
- Las señales de exit se procesan inmediatamente

Solución 3: PnL sincronizado
- El cálculo de métricas usa las mismas entradas visibles que el gráfico
- Consistencia entre lo que se muestra y lo que se calcula
```

---

## 📊 Casos de Prueba Específicos

### Caso A: Vela con Múltiples Señales

**Escenario:** Una vela de 1h contiene múltiples señales de 5m

```
Vela 1h: 10:00 - 11:00
Señales:
- 10:15 → LONG entry
- 10:35 → LONG exit
- 10:50 → SHORT entry
```

**Verificar:**
- [ ] Las 3 flechas aparecen dentro de la misma vela de 1h
- [ ] Al avanzar con playback, las 3 señales se procesan en orden
- [ ] El PnL refleja correctamente la operación LONG cerrada y SHORT abierta

---

### Caso B: Última Vela del Dataset

**Escenario:** Posición abierta en la última vela

```
Última vela con una señal LONG entry pero sin exit posterior
```

**Verificar:**
- [ ] La flecha de LONG aparece
- [ ] La posición se muestra como abierta
- [ ] El Open PnL se calcula basado en el precio de cierre de la última vela
- [ ] No hay errores en la consola

---

### Caso C: Cambio de Timeframe con Playback Activo

**Escenario:** Cambiar timeframe mientras el playback está en progreso

```
1. Iniciar playback en 5m
2. Cambiar a 1h mientras reproduce
```

**Verificar:**
- [ ] El playback se detiene o reinicia correctamente
- [ ] Las métricas se recalculan
- [ ] No hay errores en la consola del navegador

---

## 🔍 Verificación en Consola del Navegador

Abrir DevTools (F12) y verificar:

- [ ] **No hay errores** en la pestaña Console
- [ ] **No hay warnings** sobre markers o series
- [ ] **Network requests** al backend son exitosos (status 200)

---

## ✅ Criterios de Éxito

**El frontend está funcionando correctamente si:**

1. ✅ Las flechas son visibles en TODOS los timeframes (5m, 30m, 1h, 4h, 1d)
2. ✅ Las posiciones se abren cuando aparece la flecha de entrada
3. ✅ Las posiciones se cierran cuando aparece la flecha de salida
4. ✅ El PnL (Closed, Open, Total) se sincroniza con las flechas
5. ✅ El contador de trades es consistente entre timeframes
6. ✅ No hay errores en la consola del navegador
7. ✅ El playback funciona suavemente sin glitches

---

## 🚨 Si Algo No Funciona

### Debug Básico:

1. **Abrir DevTools (F12)**
2. **Ir a Console**
3. **Buscar errores rojos**
4. **Revisar Network tab** → ¿Las peticiones al backend son exitosas?

### Verificar Backend:

```bash
# Verificar que el backend esté corriendo
curl http://localhost:8000/api/symbols/

# Verificar que la estrategia responda
curl "http://localhost:8000/api/strategies/hma-sma/run/?symbol=BTCUSDT&timeframe=1h&limit=500"
```

### Hard Refresh:

- **Chrome/Edge:** Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
- **Firefox:** Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)

---

## 📝 Reporte de Resultados

Después de completar las pruebas, documenta:

```
✅ Prueba 1 (Timeframe 5m): [PASS/FAIL]
✅ Prueba 2 (Timeframe 1h): [PASS/FAIL]
✅ Prueba 3 (Playback): [PASS/FAIL]
✅ Prueba 4 (Timeframe 4h): [PASS/FAIL]
✅ Prueba 5 (Consistencia): [PASS/FAIL]
✅ Prueba 6 (Visual): [PASS/FAIL]
✅ Prueba 7 (PnL): [PASS/FAIL]

Notas adicionales:
- [Cualquier observación o comportamiento inesperado]
```

---

## 🎉 ¡Todo Listo!

El frontend está listo para probar. Si todas las pruebas pasan, los problemas de sincronización y flechas invisibles están resueltos.

**URL del frontend:** http://localhost:5173
**URL del backend:** http://localhost:8000

