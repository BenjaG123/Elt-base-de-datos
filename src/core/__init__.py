"""
Paquete CORE: Lógica de negocio y simulación.

Este paquete contiene la lógica de negocio del sistema:
- Simulación de Cyber Day
- Integración y análisis cruzado
- Analytics y métricas
"""

from src.core.analytics import *
from src.core.integration import integration_all
from src.core.simulator import CyberdaySimulator, run_simulation

__all__ = [
    "CyberdaySimulator",
    "run_simulation",
    "integration_all",
]
