"""Configuración general de estrategias e indicadores.

Este archivo centraliza:
- Qué indicadores (SMA/HMA) calculará el backend y cuáles se graficarán en el frontend.
- Qué estrategias estarán disponibles en el dropdown del frontend y cómo se llaman.
- Parámetros globales de gestión de riesgo (stop loss / take profit).

Notas:
- Para indicadores, cada timeframe puede ser un bool (legacy) o un dict con
  claves {"calc": bool, "plot": bool}. Si se usa bool: True equivale a calc+plot.
- Las estrategias aquí definidas controlan el menú del frontend a través de un endpoint
  de configuración.
"""

# Indicadores por tipo y timeframe
# - calc: el backend los calcula para tenerlos disponibles.
# - plot: el backend los expone en la respuesta para graficarlos en el frontend.
STRATEGY_INDICATORS = {
    "sma": {
        # Colores por defecto alineados con el frontend actual
        "5m": {"calc": True, "plot": True, "color": "#7c3aed", "width": 1},
        "30m": {"calc": False, "plot": False, "color": "#7c3aed", "width": 2},
        "1h": {"calc": True, "plot": True, "color": "#7c3aed", "width": 2},
        "4h": {"calc": True, "plot": True, "color": "#7c3aed", "width": 2},
        "1d": {"calc": False, "plot": False, "color": "#7c3aed", "width": 2},
    },
    "hma": {
        "5m": {"calc": False, "plot": False, "color": "#c78d06", "width": 2},
        "30m": {"calc": False, "plot": False, "color": "#c78d06", "width": 2},
        "1h": {"calc": True, "plot": True, "color": "#c78d06", "width": 2},
        "4h": {"calc": False, "plot": False, "color": "#c78d06", "width": 2},
        "1d": {"calc": True, "plot": True, "color": "#c78d06", "width": 4},
    },
}

# Estrategias disponibles en el frontend (dropdown)
# id: string usado por el backend en el query param `strategy`
# label: nombre visible en el frontend
# enabled: controla si aparece o no en el dropdown
STRATEGY_DEFINITIONS = [
    {"id": "1", "label": "Strategy 1 - Multi-timeframe", "enabled": False},
    {"id": "2", "label": "Strategy 2 - Crossover", "enabled": False},
    {"id": "3", "label": "Strategy 3 - Smart Crossover Hybrid", "enabled": False},
    {"id": "4", "label": "Estrategia 4 - 5m vs 1h", "enabled": True},
]

# Parámetros globales de gestión de riesgo
# Los porcentajes se expresan como números enteros: 2.5 = 2.5%
STOP_LOSS_ENABLED = True
STOP_LOSS_PERCENT = 10.0

TAKE_PROFIT_ENABLED = False
TAKE_PROFIT_PERCENT = 20.0
