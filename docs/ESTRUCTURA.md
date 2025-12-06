# 📁 Estructura del Proyecto ETL

## Organización de Carpetas

```
Elt-base-de-datos/
│
├── src/                        # Código fuente principal
│   ├── etl/                    # Módulos ETL (Extract, Transform, Load)
│   │   ├── __init__.py
│   │   ├── extract.py          # Extracción de datos desde CSVs
│   │   ├── transform.py        # Limpieza y transformación de datos
│   │   └── load.py             # Carga a MongoDB y Redis
│   │
│   ├── core/                   # Lógica de negocio principal
│   │   ├── __init__.py
│   │   ├── simulator.py        # Simulador de Cyber Day
│   │   ├── integration.py      # Análisis cruzado MongoDB + Redis
│   │   └── analytics.py        # Métricas y analytics avanzados
│   │
│   ├── visualization/          # Generación de gráficos y reportes
│   │   ├── __init__.py
│   │   └── charts.py           # Visualizaciones con matplotlib
│   │
│   ├── utils/                  # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── helpers.py          # Funciones helper (conversiones, limpieza)
│   │   └── validators.py       # Validadores de datos (futuro)
│   │
│   ├── config/                 # Configuraciones del sistema
│   │   ├── __init__.py
│   │   ├── database.py         # Conexiones MongoDB y Redis
│   │   └── constants.py        # Constantes globales (futuro)
│   │
│   └── __init__.py
│
├── data/                       # Datos del proyecto
│   ├── raw/                    # Datos crudos sin procesar
│   │   ├── amazon.csv
│   │   └── redis_cart_sim.csv
│   ├── processed/              # Datos procesados y limpios
│   │   ├── amazon_processed.csv
│   │   └── carts_processed.csv
│   └── output/                 # Resultados y visualizaciones
│       └── *.png               # Gráficos generados
│
├── tests/                      # Tests unitarios y de integración
│   ├── __init__.py
│   ├── test_etl/               # Tests de ETL
│   ├── test_core/              # Tests de lógica de negocio
│   └── test_utils/             # Tests de utilidades
│
├── docs/                       # Documentación del proyecto
│   ├── ESTRUCTURA.md           # Este archivo
│   └── architecture.md         # Arquitectura del sistema
│
├── scripts/                    # Scripts auxiliares
│   ├── setup_databases.py      # Setup de MongoDB y Redis
│   └── clean_data.py           # Limpieza de datos
│
├── req/                        # Requisitos y documentación académica
│   └── Proyecto Final.pdf
│
├── main.py                     # Entry point del pipeline completo
├── requirements.txt            # Dependencias de Python
├── README.md                   # Documentación principal
└── .gitignore                  # Archivos ignorados por Git
```

## 📦 Descripción de Paquetes

### `src/etl/` - Pipeline ETL Principal
**Responsabilidad**: Extracción, transformación y carga de datos.

**Módulos**:
- `extract.py`: Lee datos desde archivos CSV
- `transform.py`: Limpia y normaliza datos (precios, fechas, validaciones)
- `load.py`: Persiste datos en MongoDB y Redis + CSVs de auditoría

**Principios aplicados**:
- Cada módulo tiene una sola responsabilidad (SRP)
- Sin lógica de negocio, solo transformaciones técnicas

---

### `src/core/` - Lógica de Negocio
**Responsabilidad**: Simulación, integración y análisis de negocio.

**Módulos**:
- `simulator.py`: Simula eventos de Cyber Day en tiempo real
- `integration.py`: Análisis cruzado entre MongoDB y Redis
- `analytics.py`: Métricas de negocio y KPIs

**Principios aplicados**:
- Separación de lógica de negocio del ETL
- Reutilización de componentes

---

### `src/visualization/` - Reportes y Gráficos
**Responsabilidad**: Generación de visualizaciones.

**Módulos**:
- `charts.py`: Gráficos con matplotlib/seaborn

**Principios aplicados**:
- Separación de presentación de datos
- Fácil extensión para nuevos tipos de gráficos

---

### `src/utils/` - Utilidades Compartidas
**Responsabilidad**: Funciones auxiliares reutilizables.

**Módulos**:
- `helpers.py`: Conversiones, limpieza de formatos, persistencia
- `validators.py`: Validadores de datos (futuro)

**Principios aplicados**:
- DRY (Don't Repeat Yourself)
- Funciones puras y testeables

---

### `src/config/` - Configuraciones
**Responsabilidad**: Configuración centralizada del sistema.

**Módulos**:
- `database.py`: Conexiones a MongoDB y Redis
- `constants.py`: Constantes globales (futuro)

**Principios aplicados**:
- Configuración centralizada
- Fácil modificación de parámetros

---

## 🚀 Flujo de Ejecución

```
main.py
   ↓
   ├─→ src.config (get_mongo_connection, get_redis_connection)
   ├─→ src.etl.extract (extract_all)
   ├─→ src.etl.transform (transform_all)
   ├─→ src.etl.load (load_all)
   ├─→ src.core.simulator (run_simulation)
   ├─→ src.core.integration (integration_all)
   └─→ src.visualization (generate_all_visualizations)
```

## 📊 Ventajas de esta Estructura

✅ **Modularidad**: Cada paquete tiene una responsabilidad clara
✅ **Escalabilidad**: Fácil agregar nuevos módulos sin afectar existentes
✅ **Mantenibilidad**: Código organizado y fácil de encontrar
✅ **Testabilidad**: Estructura facilita tests unitarios
✅ **Profesionalismo**: Sigue estándares de la industria
✅ **Colaboración**: Múltiples desarrolladores pueden trabajar sin conflictos

## 🔄 Migración desde Estructura Anterior

### Cambios realizados:

| Archivo Anterior | Nuevo Ubicación |
|-----------------|-----------------|
| `src/extract.py` | `src/etl/extract.py` |
| `src/transform.py` | `src/etl/transform.py` |
| `src/load.py` | `src/etl/load.py` |
| `src/simulator.py` | `src/core/simulator.py` |
| `src/integration.py` | `src/core/integration.py` |
| `src/analytics.py` | `src/core/analytics.py` |
| `src/visualizations.py` | `src/visualization/charts.py` |
| `src/utils.py` | `src/utils/helpers.py` |
| `src/config.py` | `src/config/database.py` |

### Imports actualizados:

```python
# ❌ Antes
from src.extract import extract_all
from src.transform import transform_all
from src.load import load_all

# ✅ Ahora
from src.etl import extract_all, transform_all, load_all
```

---

## 📝 Próximos Pasos

1. ✅ Crear tests unitarios en `tests/`
2. ✅ Agregar `src/config/constants.py` con constantes de negocio
3. ✅ Agregar `src/utils/validators.py` con validadores
4. ✅ Documentar arquitectura en `docs/architecture.md`
5. ✅ Crear scripts de setup en `scripts/`

---

**Autor**: ETL Team
**Fecha**: Diciembre 2025
**Versión**: 2.0 (Estructura refactorizada)
