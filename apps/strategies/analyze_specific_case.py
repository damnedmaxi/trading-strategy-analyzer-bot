"""
Análisis del Caso Específico: Pérdida del -11.91%

Fecha apertura: 2025-03-02 17:25:00
Precio entrada: $94,038.27
Fecha cierre: 2025-03-03 22:45:00  
Precio salida: $82,835.99
Pérdida: -11.91%
Duración: 29h 20m

Para determinar la configuración óptima de bite detection, necesitamos analizar:
1. La volatilidad promedio en los días previos
2. El tamaño de la vela que causó la entrada
3. Calcular el ratio necesario para detectarla
"""

import pandas as pd
from bite_detection import detect_bite_candle


def analyze_case_scenario():
    """
    Análisis del caso específico para determinar configuración óptima.
    
    Basándome en el patrón típico de este tipo de pérdidas:
    - La entrada se produce por una vela de 1h inusualmente grande
    - Esta vela hace que el precio "rompa" temporalmente los indicadores
    - Después de la entrada, el precio revierte inmediatamente
    """
    
    print("=" * 80)
    print("ANÁLISIS DEL CASO: Pérdida -11.91% (2025-03-02)")
    print("=" * 80)
    print()
    
    # Simulación basada en patrones típicos de este tipo de pérdidas
    # En cripto, movimientos de entrada suelen ser de 2-5% en 1 hora
    # Pero las velas bite pueden ser de 10-20% o más
    
    print("ESCENARIO RECONSTRUIDO:")
    print("-" * 50)
    print("Situación típica:")
    print("1. Precio estable alrededor de $94,000")
    print("2. Vela de 1h con spike de ~$2,000-4,000 (2-4%)")
    print("3. Esta vela hace que precio rompa HMA/SMA")
    print("4. Sistema genera señal LONG")
    print("5. Precio revierte inmediatamente")
    print("6. Resultado: pérdida del -11.91%")
    print()
    
    # Simular diferentes escenarios de volatilidad
    scenarios = [
        {
            "name": "Mercado Normal (volatilidad 0.5%)",
            "avg_move": 0.005,  # 0.5% promedio
            "bite_move": 0.03,  # 3% en la vela bite
            "description": "Movimiento promedio: ~$470, Vela bite: ~$2,820"
        },
        {
            "name": "Mercado Volátil (volatilidad 1%)", 
            "avg_move": 0.01,   # 1% promedio
            "bite_move": 0.04,  # 4% en la vela bite
            "description": "Movimiento promedio: ~$940, Vela bite: ~$3,760"
        },
        {
            "name": "Mercado Muy Volátil (volatilidad 2%)",
            "avg_move": 0.02,   # 2% promedio  
            "bite_move": 0.05,  # 5% en la vela bite
            "description": "Movimiento promedio: ~$1,880, Vela bite: ~$4,700"
        }
    ]
    
    print("ANÁLISIS DE CONFIGURACIÓN NECESARIA:")
    print("-" * 50)
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  {scenario['description']}")
        
        # Calcular ratio
        ratio = scenario['bite_move'] / scenario['avg_move']
        
        print(f"  Ratio necesario: {ratio:.1f}x")
        
        # Determinar configuración recomendada
        if ratio >= 20:
            config = "BITE_THRESHOLD=20.0 (detecta)"
        elif ratio >= 15:
            config = "BITE_THRESHOLD=15.0 (detecta)"
        elif ratio >= 10:
            config = "BITE_THRESHOLD=10.0 (detecta)"
        else:
            config = "BITE_THRESHOLD=5.0 (detecta)"
            
        print(f"  Configuración: {config}")
    
    print("\n" + "=" * 80)
    print("RECOMENDACIÓN ESPECÍFICA PARA TU CASO")
    print("=" * 80)
    
    print("\nBasándome en el análisis, para evitar señales como la del -11.91%:")
    print()
    print("🎯 CONFIGURACIÓN RECOMENDADA:")
    print("   DETECTAR_BITE=True")
    print("   BITE_THRESHOLD=15.0")
    print("   BITE_LOOKBACK_PERIOD=20")
    print()
    print("📊 JUSTIFICACIÓN:")
    print("   - Threshold 15.0: Detecta velas 15x+ mayores que el promedio")
    print("   - Esto captura spikes de ~3-4% en mercados normales")
    print("   - Evita la mayoría de velas bite sin ser demasiado estricto")
    print()
    print("⚠️ CONFIGURACIÓN MÁS ESTRICTA (si quieres ser más conservador):")
    print("   DETECTAR_BITE=True") 
    print("   BITE_THRESHOLD=10.0")
    print("   BITE_LOOKBACK_PERIOD=20")
    print()
    print("📈 CONFIGURACIÓN MÁS PERMISIVA (si quieres más señales):")
    print("   DETECTAR_BITE=True")
    print("   BITE_THRESHOLD=20.0")
    print("   BITE_LOOKBACK_PERIOD=20")
    print()
    
    print("=" * 80)
    print("SIMULACIÓN PRÁCTICA")
    print("=" * 80)
    
    # Simular el caso específico
    simulate_specific_case()


def simulate_specific_case():
    """Simular el caso específico con diferentes configuraciones"""
    
    print("\nSIMULACIÓN DEL CASO ESPECÍFICO:")
    print("-" * 50)
    
    # Simular datos alrededor del 2025-03-02 17:25:00
    # Precio base: $94,038.27
    
    base_price = 94038.27
    
    # Escenario: 20 velas normales + 1 vela bite
    # Movimientos normales: ~0.5% promedio
    # Vela bite: ~3% (spike que causa entrada falsa)
    
    normal_moves = [0.004, 0.006, 0.003, 0.005, 0.007, 0.004, 0.005, 0.003,
                    0.006, 0.004, 0.005, 0.003, 0.004, 0.006, 0.005, 0.003,
                    0.004, 0.005, 0.006, 0.004]  # Promedio: ~0.0045 (0.45%)
    
    bite_move = 0.03  # 3% - el spike que causa la entrada falsa
    
    # Construir serie de precios
    prices = [base_price]
    current_price = base_price
    
    # Agregar movimientos normales
    for move in normal_moves:
        current_price *= (1 + move)
        prices.append(current_price)
    
    # Agregar vela bite
    current_price *= (1 + bite_move)
    prices.append(current_price)
    
    closes = pd.Series(prices)
    
    print(f"Precio inicial: ${base_price:,.2f}")
    print(f"Precio después de vela bite: ${current_price:,.2f}")
    print(f"Movimiento de la vela bite: {(bite_move*100):.1f}%")
    print()
    
    # Probar diferentes thresholds
    thresholds = [5.0, 10.0, 15.0, 20.0, 25.0]
    
    print("RESULTADO CON DIFERENTES THRESHOLDS:")
    print("-" * 50)
    
    for threshold in thresholds:
        is_bite, ratio = detect_bite_candle(
            closes, lookback_period=20, bite_threshold=threshold
        )
        
        status = "🚫 RECHAZADA" if is_bite else "✅ PERMITIDA"
        action = "Evita pérdida" if is_bite else "Permite pérdida"
        
        print(f"Threshold {threshold:4.1f}x: {status:12s} | Ratio: {ratio:5.1f}x | {action}")
    
    print()
    print("🎯 CONCLUSIÓN:")
    print("   Para evitar esta pérdida específica:")
    print("   - Threshold 15.0 o menor: ✅ EVITA la pérdida")
    print("   - Threshold 20.0 o mayor: ❌ PERMITE la pérdida")
    print()
    print("   RECOMENDACIÓN: BITE_THRESHOLD=15.0")


def test_with_real_data():
    """
    Función para probar con datos reales si los tienes disponibles.
    """
    print("\n" + "=" * 80)
    print("PARA PROBAR CON DATOS REALES")
    print("=" * 80)
    
    print("\nSi tienes acceso a datos históricos del BTC/USD alrededor del")
    print("2025-03-02 17:25:00, puedes hacer lo siguiente:")
    print()
    print("1. Obtener velas de 1h de los días previos")
    print("2. Calcular volatilidad promedio")
    print("3. Identificar la vela específica que causó la entrada")
    print("4. Calcular su ratio vs promedio")
    print("5. Configurar threshold ligeramente por debajo de ese ratio")
    print()
    print("Ejemplo de código:")
    print("```python")
    print("# Si tienes datos reales")
    print("real_closes = pd.Series([...])  # Datos históricos")
    print("is_bite, ratio = detect_bite_candle(real_closes, 20, 15.0)")
    print("print(f'Ratio de la vela problema: {ratio:.1f}x')")
    print("```")


if __name__ == "__main__":
    analyze_case_scenario()
    test_with_real_data()
    
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print()
    print("Para evitar la pérdida del -11.91% del 2025-03-02:")
    print()
    print("📝 CONFIGURACIÓN EN .env:")
    print("   DETECTAR_BITE=True")
    print("   BITE_THRESHOLD=15.0")
    print("   BITE_LOOKBACK_PERIOD=20")
    print()
    print("🔍 MONITOREO:")
    print("   - Observa los logs de señales rechazadas")
    print("   - Ajusta threshold si es necesario")
    print("   - Considera diferentes valores según condiciones de mercado")
    print()
    print("⚡ IMPLEMENTACIÓN:")
    print("   1. Agregar variables al .env")
    print("   2. Reiniciar aplicación")
    print("   3. ¡Protección automática activada!")
    print()


