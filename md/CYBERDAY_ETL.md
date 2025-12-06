# 🚀 Pipeline ETL: Cyberday con MongoDB y Redis

Sistema completo de ETL para simular un **Cyberday** con múltiples productos y carritos de compra en tiempo real.

## 📋 Descripción

Este proyecto implementa:

- **MongoDB**: Almacena el catálogo de productos (Flipkart dataset)
- **Redis**: Gestiona carritos y eventos en tiempo real
- **Pipeline ETL**: Extract → Transform → Load → Integration
- **Análisis**: Métricas de conversión, ingresos, abandono de carritos

## 📊 Datasets

### 1. Flipkart (MongoDB)
- **Archivo**: `data/raw/flipkart_com-ecommerce_sample.csv`
- **Contenido**: Catálogo de productos públicos de Flipkart
- **Campos**: Nombre, precio, marca, categoría, descuento, etc.
- **Uso**: Base de datos de productos para simular un e-commerce

### 2. Redis Cart Simulation
- **Archivo**: `data/raw/redis_cart_sim.csv`
- **Contenido**: Eventos simulados de carritos de compra
- **Campos**: 
  - `cart_id`: ID único del carrito
  - `customer_id`: Cliente
  - `event_time`: Momento del evento
  - `event_type`: add, checkout, abandon, stock_out
  - `product_id`: Producto agregado/comprado
  - `quantity`: Cantidad
  - `revenue`: Ingresos generados
  - `lost_revenue`: Ingresos perdidos
- **Uso**: Simulación en tiempo real de transacciones

## 🏗️ Arquitectura ETL

```
┌─────────────────────────────────────────────────────────────┐
│                       EXTRACT                               │
│  Flipkart CSV ──────┐  Redis Cart CSV ──────┐               │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                      TRANSFORM                              │
│  - Limpieza de datos      - Validación de tipos             │
│  - Normalización          - Cálculo de descuentos           │
│  - Estadísticas           - Transformación de eventos       │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                        LOAD                                 │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   MongoDB    │         │    Redis     │                  │
│  │  Productos   │         │  Carritos    │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    INTEGRATION                              │
│  - Enriquecimiento de datos                                 │
│  - Análisis cruzado MongoDB ↔ Redis                         │
│  - Métricas del Cyberday                                    │
│  - Generación de reportes                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Requisitos Previos

### Software Necesario
```bash
# Instalar MongoDB Community
# https://docs.mongodb.com/manual/installation/

# Instalar Redis
# https://redis.io/download/
```

### Python 3.8+
```bash
pip install -r requirements.txt
```

**Dependencias**:
- `pymongo`: Cliente Python para MongoDB
- `redis`: Cliente Python para Redis
- `pandas`: Manipulación de datos
- `matplotlib`: Visualizaciones
- `seaborn`: Gráficos estadísticos
- `plotly`: Gráficos interactivos

## 🚀 Uso

### 1. Iniciar servicios (en terminales separadas)

```bash
# Terminal 1: MongoDB
mongod

# Terminal 2: Redis
redis-server
```

### 2. Ejecutar el pipeline ETL completo

```bash
python main.py
```

Esto ejecutará:
1. **EXTRACT**: Carga ambos CSVs
2. **TRANSFORM**: Limpia y transforma datos
3. **LOAD**: Carga en MongoDB y Redis
4. **INTEGRATION**: Genera análisis y reportes

### 3. Ejecutar etapas individuales

```bash
# Solo extracción
python -m src.extract

# Solo transformación
python -m src.transform

# Solo carga
python -m src.load

# Solo análisis
python -m src.integration

# Visualizaciones
python -m src.visualizations
```

## 📈 Salida del Pipeline

### Ejemplo de ejecución exitosa:

```
======================================================================
 🚀 PIPELINE ETL: CYBERDAY CON MONGODB Y REDIS
Inicio: 2025-12-05 14:30:45
======================================================================

======================================================================
 📥 ETAPA 1: EXTRACT (Extracción)
======================================================================
[EXTRACT] Leído 6 filas de data/raw/flipkart_com-ecommerce_sample.csv
[EXTRACT] Leído 15 filas de data/raw/redis_cart_sim.csv

[EXTRACT] Productos Flipkart: 6 registros
          product_name discounted_price             brand
0  Alisha Solid Women's Cycling Shorts           379.0           Alisha

[EXTRACT] Eventos de carrito: 15 eventos
  cart_id event_type product_id  quantity
0  CART-001        add     P-1001         1

======================================================================
 📤 ETAPA 3: LOAD (Carga a MongoDB y Redis)
======================================================================
Conectado a MongoDB
[LOAD] Colección limpiada
[LOAD] 6 productos cargados a MongoDB
Conectado a Redis
[LOAD] Redis limpiado
[LOAD] 5 carritos cargados a Redis

======================================================================
 📊 RESUMEN DEL PIPELINE
======================================================================
✅ Productos Flipkart: 6
✅ Eventos de Carrito: 15
✅ Carritos Únicos: 5
✅ Clientes: 5
💰 Ingresos Totales: $20571.00
❌ Ingresos Perdidos: $8997.00

✨ Pipeline completado exitosamente
```

## 📊 Datos Almacenados

### MongoDB - Colección `flipkart_products`

```javascript
{
  "_id": ObjectId(...),
  "uniq_id": "c2d766ca...",
  "product_name": "Alisha Solid Women's Cycling Shorts",
  "pid": "SRTEH2FF9KEDEFGF",
  "retail_price": 999,
  "discounted_price": 379,
  "discount_percent": 62.06,
  "brand": "Alisha",
  "main_category": "Clothing",
  "stock": 100,
  "total_sales": 0,
  "created_at": ISODate("2025-12-05T14:30:45.123Z")
}
```

### Redis - Keys de Carrito

```
cart:CART-001
  - customer_id: CUST-01
  - events: [JSON array de eventos]
  - total_revenue: 3577
  - lost_revenue: 0
  - loaded_at: 2025-12-05T14:30:45

cart:realtime:CART-001:add
  - [evento en tiempo real]
```

## 📊 Métricas Generadas

### Reporte del Cyberday

| Métrica | Valor |
|---------|-------|
| Total de Productos | 6 |
| Total de Carritos | 5 |
| Carritos Completados | 3 |
| Carritos Abandonados | 1 |
| Ingresos Totales | $20,571.00 |
| Ingresos Perdidos | $8,997.00 |
| Tasa de Conversión | 60.00% |
| Tasa de Abandono | 20.00% |

## 🔄 Funcionalidades Principales

### EXTRACT (`src/extract.py`)
- Carga Flipkart CSV para MongoDB
- Carga CSV de simulación de carritos para Redis
- Validación y vista previa de datos

### TRANSFORM (`src/transform.py`)
- Normalización de precios y valores
- Limpieza de datos NULL
- Cálculo de descuentos y estadísticas
- Validación de rangos de datos

### LOAD (`src/load.py`)
- Inserción masiva en MongoDB
- Almacenamiento en Redis con estructura JSON
- Simulación opcional en tiempo real

### INTEGRATION (`src/integration.py`)
- Análisis de productos por marca
- Métricas de carritos en tiempo real
- Enriquecimiento de datos cruzados
- Generación de reportes

### VISUALIZATIONS (`src/visualizations.py`)
- Distribución de productos por marca
- Distribución de precios
- Línea de tiempo de eventos
- Métricas de ingresos

## 🔍 Consultas Útiles

### MongoDB
```javascript
// Top marcas
db.flipkart_products.aggregate([
  { $group: { _id: "$brand", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Productos con descuento > 50%
db.flipkart_products.find({ discount_percent: { $gt: 50 } })

// Precio promedio por marca
db.flipkart_products.aggregate([
  { $group: { _id: "$brand", avg_price: { $avg: "$discounted_price" } } }
])
```

### Redis (CLI)
```bash
# Ver carritos
KEYS cart:CART-*

# Detalles de carrito
HGETALL cart:CART-001

# Eventos de carrito
HGET cart:CART-001 events

# Estadísticas
INFO stats
```

## 🐛 Troubleshooting

### Error: "No se puede conectar a MongoDB"
```bash
# Verificar que MongoDB esté ejecutándose
mongod --version

# Iniciar MongoDB
mongod
```

### Error: "No se puede conectar a Redis"
```bash
# Verificar que Redis esté ejecutándose
redis-server --version

# Iniciar Redis
redis-server
```

### Error: "No se encontró el archivo CSV"
```
Asegúrate de que los archivos están en:
- data/raw/flipkart_com-ecommerce_sample.csv
- data/raw/redis_cart_sim.csv
```

## 📁 Estructura del Proyecto

```
.
├── main.py                          # Orquestador principal
├── requirements.txt                 # Dependencias Python
├── CYBERDAY_ETL.md                 # Este archivo
├── data/
│   ├── raw/
│   │   ├── flipkart_com-ecommerce_sample.csv
│   │   └── redis_cart_sim.csv
│   └── processed/
│       ├── flipkart_processed.csv
│       ├── brands_distribution.png
│       ├── price_distribution.png
│       ├── cart_events.png
│       └── revenue_metrics.png
├── src/
│   ├── __init__.py
│   ├── config.py                    # Configuración de conexiones
│   ├── extract.py                   # Extracción de datos
│   ├── transform.py                 # Transformación de datos
│   ├── load.py                      # Carga a bases de datos
│   ├── integration.py               # Análisis cruzado
│   └── visualizations.py            # Generación de gráficos
└── docs/
    └── images/
```

## 🎯 Casos de Uso

### Caso 1: Simular Cyberday
```python
from src.load import load_all
load_all(products_df, carts_df)
```

### Caso 2: Analizar conversiones
```python
from src.integration import generate_cyberday_report
report = generate_cyberday_report()
```

### Caso 3: Encontrar carritos abandonados
```python
from src.config import get_redis_connection
r = get_redis_connection()
carts = r.keys("cart:CART-*")
for cart in carts:
    events = r.hget(cart, "events")
    # Buscar eventos con "abandon"
```

## 📝 Notas Importantes

1. **Datos Simulados**: El CSV de carritos contiene datos simulados para demostración
2. **Escalabilidad**: Para producción, ajusta tamaños de lotes en `load_all()`
3. **Tiempo Real**: La simulación puede configurarse en `load.py` con delays reales
4. **Seguridad**: Usa variables de entorno para credenciales en producción

## 📞 Soporte

Para problemas o preguntas, revisa:
- Logs en la consola durante ejecución
- Estado de MongoDB/Redis con `mongosh` y `redis-cli`
- Archivos CSV en `data/raw/`

## ✅ Checklist de Verificación

- [ ] MongoDB está ejecutándose (`mongod`)
- [ ] Redis está ejecutándose (`redis-server`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivos CSV en `data/raw/`
- [ ] Carpeta `data/processed/` existe
- [ ] Ejecutar `python main.py`
- [ ] Verificar salida en MongoDB/Redis

---

**Versión**: 1.0  
**Última actualización**: 2025-12-05  
**Autor**: ETL Pipeline  
