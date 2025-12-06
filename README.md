# 🚀 Pipeline ETL: Cyberday con MongoDB y Redis

Simulación completa de un **Cyberday** con múltiples productos y carritos de compra en tiempo real, utilizando:
- **MongoDB** para el catálogo de productos (Flipkart dataset)
- **Redis** para carritos y eventos en tiempo real

## 🎯 Inicio Rápido

### 1. Verificar requisitos
```bash
python diagnose.py
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Iniciar servicios
```bash
# Terminal 1: MongoDB
mongod

# Terminal 2: Redis  
redis-server
```

### 4. Ejecutar pipeline
```bash
python main.py
```

## 📊 Datasets

### Flipkart Products (MongoDB)
- **Archivo**: `data/raw/flipkart_com-ecommerce_sample.csv`
- **Contenido**: ~6 productos con precios, marcas, categorías
- **Uso**: Catálogo para simular e-commerce

### Redis Cart Simulation
- **Archivo**: `data/raw/redis_cart_sim.csv`
- **Contenido**: ~15 eventos de carritos simulados
- **Eventos**: add, checkout, abandon, stock_out
- **Uso**: Simular transacciones en tiempo real

## 🏗️ Flujo ETL

```
EXTRACT      TRANSFORM     LOAD           INTEGRATION
   ↓            ↓           ↓                 ↓
CSV Files → Clean Data → MongoDB ────→ Análisis Cruzado
              Normalize      Redis ────→ Reportes
                Validate    + Stats   Visualizaciones
```

## 📈 Salida Esperada

```
✅ Productos Flipkart: 6
✅ Eventos de Carrito: 15  
✅ Carritos Únicos: 5
✅ Clientes: 5
💰 Ingresos Totales: $20,571.00
❌ Ingresos Perdidos: $8,997.00
📊 Tasa de Conversión: 60%
```

## 📚 Documentación Completa

Ver [CYBERDAY_ETL.md](CYBERDAY_ETL.md) para:
- Arquitectura detallada
- Consultas de ejemplo
- Troubleshooting
- Casos de uso avanzados

## 🛠️ Módulos

| Módulo | Descripción |
|--------|------------|
| `src/extract.py` | Carga datos de CSVs |
| `src/transform.py` | Limpia y normaliza datos |
| `src/load.py` | Carga en MongoDB y Redis |
| `src/integration.py` | Análisis cruzado y reportes |
| `src/visualizations.py` | Genera gráficos |
| `src/config.py` | Configuración centralizada |

## ✨ Características

- ✅ ETL completo: Extract → Transform → Load → Integration
- ✅ MongoDB para almacenamiento persistente de productos
- ✅ Redis para datos en tiempo real
- ✅ Simulación de Cyberday con múltiples clientes
- ✅ Métricas de conversión y abandono de carritos
- ✅ Visualizaciones automáticas
- ✅ Enriquecimiento cruzado de datos MongoDB ↔ Redis

## 🔍 Ejemplo de Uso

```python
from main import main
main()  # Ejecuta el pipeline completo
```

O ejecuta etapas específicas:

```python
from src.extract import extract_all
from src.transform import transform_all
from src.load import load_all
from src.integration import integration_all

# Extraer
flipkart_df, redis_cart_df = extract_all()

# Transformar
flipkart_tf, cart_tf = transform_all()

# Cargar
load_all(products_df, carts_df)

# Analizar
report = integration_all()
```

## 📊 Estructura de Datos

### MongoDB
```javascript
{
  "product_name": "Alisha Cycling Shorts",
  "pid": "SRTEH2FF9KEDEFGF",
  "discounted_price": 379,
  "retail_price": 999,
  "discount_percent": 62.06,
  "brand": "Alisha",
  "stock": 100,
  "created_at": "2025-12-05T14:30:45.123Z"
}
```

### Redis
```
cart:CART-001
├── customer_id: CUST-01
├── events: [{event_type, product_id, quantity, revenue}, ...]
├── total_revenue: 3577
└── lost_revenue: 0
```

## 🐛 Troubleshooting

**MongoDB no conecta**
```bash
mongod  # Inicia el servicio
```

**Redis no conecta**
```bash
redis-server  # Inicia el servicio
```

**Módulos no encontrados**
```bash
pip install -r requirements.txt
```

## 📝 Ver también

- [CYBERDAY_ETL.md](CYBERDAY_ETL.md) - Documentación completa
- `diagnose.py` - Script de diagnóstico
