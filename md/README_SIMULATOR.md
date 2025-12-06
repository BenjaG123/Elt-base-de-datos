# 🚀 SIMULADOR CYBER DAY - Amazon Products

Simulación completa de un **Cyberday** con:
- **MongoDB** para el catálogo de productos (Dataset Amazon)
- **Redis** para carritos y eventos en tiempo real

## 🎯 ¿Qué hace este proyecto?

1. **Carga productos Amazon a MongoDB** (1467 productos reales)
2. **Simula un Cyber Day** con compras en tiempo real
3. **Calcula métricas clave:**
   - Productos más vendidos
   - Categorías más vendidas
   - Dinero perdido por falta de stock
   - Productos más cotizados (se agotaron más rápido)
   - Comportamiento de clientes
4. **Genera visualizaciones** automáticas

---

## 📋 Requisitos Previos

### 1. Instalar MongoDB
```bash
# Windows: Descargar de https://www.mongodb.com/try/download/community
# Iniciar servicio:
mongod
```

### 2. Instalar Redis
```bash
# Windows: Descargar de https://redis.io/download
# o usar Redis Stack: https://redis.io/download#redis-stack-downloads
# Iniciar servicio:
redis-server
```

### 3. Instalar Python (3.8+)
```bash
python --version  # Verificar versión
```

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Verificar configuración
```bash
python diagnose.py
```

### 3. Ejecutar simulación completa
```bash
python main.py
```

Esto ejecutará:
1. Carga de 1467 productos Amazon a MongoDB
2. Simulación de 500 eventos de compra con 100 clientes
3. Análisis completo de resultados
4. Generación de gráficos

---

## 📊 Resultados

### Archivos generados:

```
data/processed/
├── cyberday_simulation.csv          # Todos los eventos simulados
├── top_selling_products.png         # Top 15 productos vendidos
├── top_categories.png               # Top 10 categorías
├── lost_revenue_by_category.png     # Pérdidas por categoría
├── stock_out_times.png              # Productos más cotizados
└── revenue_comparison.png           # Ingresos vs Pérdidas
```

### Ejemplo de salida:

```
📊 ANÁLISIS: Productos más vendidos
----------------------------------------------------------------------
Ambrane Unbreakable 60W / 3A Fast...     15    ₹5,985
boAt A400 USB Type-C to USB-A 2.0...     12    ₹3,588
MI Usb Type-C Cable Smartphone (Bl...     10    ₹2,290

💰 ANÁLISIS: Dinero perdido
----------------------------------------------------------------------
💵 TOTAL PERDIDO: ₹45,123.00
💵 TOTAL VENDIDO: ₹123,456.00
📊 % PERDIDO: 26.8%

⏱️  ANÁLISIS: Tiempo de agotamiento
----------------------------------------------------------------------
🔥 PRODUCTOS MÁS COTIZADOS (se agotaron más rápido):
1. TP-Link USB WiFi Adapter         2.3 minutos
2. AmazonBasics HDMI Cable           3.1 minutos
3. boAt Deuce USB 300                4.5 minutos
```

---

## 🔧 Personalizar la Simulación

### Ajustar parámetros en `main.py`:

```python
simulation_df = run_simulation(
    num_customers=100,  # Número de clientes
    num_events=500,     # Número de eventos de compra
    save_csv=True       # Guardar en CSV
)
```

### Ejecutar solo el simulador:

```python
python src/simulator.py
```

### Ejecutar solo el análisis:

```python
python src/analytics.py
```

### Generar solo visualizaciones:

```python
python src/visualizations.py
```

---

## 📈 Consultas Implementadas

### 1. Productos más vendidos
```python
from src.analytics import CyberdayAnalytics
analytics = CyberdayAnalytics()
analytics.connect()
top_products = analytics.get_top_selling_products(limit=10)
```

### 2. Categorías más vendidas
```python
top_categories = analytics.get_top_categories()
```

### 3. Dinero perdido
```python
lost_analysis = analytics.get_lost_revenue_analysis()
# Retorna:
# - Total perdido
# - Total vendido
# - % perdido
# - Top productos con pérdidas
# - Top categorías con pérdidas
```

### 4. Productos más cotizados (agotados más rápido)
```python
fastest_to_stock_out = analytics.get_stock_out_times()
```

### 5. Comportamiento de clientes
```python
customer_behavior = analytics.get_customer_behavior()
```

---

## 🗄️ Estructura de Datos

### MongoDB (Catálogo)
```javascript
{
  "product_id": "B07JW9H4J1",
  "product_name": "Wayona Nylon Braided USB...",
  "category": "Computers&Accessories|...",
  "discounted_price": 399,
  "actual_price": 1099,
  "discount_percentage": 64,
  "rating": 4.2,
  "stock": 100,
  "total_sales": 0,
  "created_at": "2025-12-05..."
}
```

### Redis (Carritos)
```
cart:CART-001
├── customer_id: CUST-01
├── events: [{event_type, product_id, quantity, revenue, lost_revenue}, ...]
├── total_revenue: 3577
└── lost_revenue: 0

stock_out:B07JW9H4J1
├── product_name: "Wayona Nylon Braided..."
├── category: "Computers&Accessories"
├── duration_seconds: 145.3
└── time: "2025-12-05T22:15:23"
```

---

## 🔍 Análisis de Cruce MongoDB ↔ Redis

El proyecto implementa **12 tipos de cruces**:

1. **Lookup**: Redis busca info de producto en MongoDB
2. **Enriquecimiento**: MongoDB enriquece eventos de Redis
3. **Sincronización de stock**: Actualización bidireccional
4. **Validación**: MongoDB valida disponibilidad
5. **Analytics**: Combina métricas de ambas BDs

Ver detalles completos en: [`CRUCES_DE_INFORMACION.md`](CRUCES_DE_INFORMACION.md)

---

## 📁 Estructura del Proyecto

```
Elt-base-de-datos/
├── data/
│   ├── raw/
│   │   ├── amazon.csv              # Dataset Amazon (1467 productos)
│   │   └── redis_cart_sim.csv      # (deprecado, ahora se usa simulador)
│   └── processed/
│       ├── cyberday_simulation.csv
│       └── *.png                   # Gráficos
├── src/
│   ├── config.py                   # Configuración MongoDB/Redis
│   ├── extract.py                  # Carga de datos
│   ├── transform.py                # Limpieza de datos
│   ├── load.py                     # Carga a MongoDB
│   ├── simulator.py                # ⭐ SIMULADOR CYBER DAY
│   ├── analytics.py                # ⭐ ANÁLISIS COMPLETO
│   └── visualizations.py           # Gráficos
├── main.py                         # ⭐ EJECUTAR TODO
├── requirements.txt
└── README.md
```

---

## 🐛 Troubleshooting

### MongoDB no conecta
```bash
# Verificar que esté corriendo:
mongod

# En otra terminal:
mongo
```

### Redis no conecta
```bash
# Verificar que esté corriendo:
redis-server

# En otra terminal:
redis-cli ping
# Debe responder: PONG
```

### Error: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Ver datos en MongoDB
```bash
mongo
> use amazon_db
> db.amazon_products.find().pretty()
> db.amazon_products.countDocuments()
```

### Ver datos en Redis
```bash
redis-cli
> KEYS *
> HGETALL cart:CART-001
> KEYS stock_out:*
```

---

## 📊 Métricas del Proyecto

Este proyecto cumple con los requisitos del Cyber Day ETL:

✅ **2 Bases de Datos NoSQL**: MongoDB + Redis  
✅ **Dataset Público**: Amazon Products (1467 productos)  
✅ **ETL Completo**: Extract → Transform → Load → Integration  
✅ **Consultas Implementadas**:
- Productos más vendidos
- Categorías más vendidas
- Dinero perdido (por producto y categoría)
- Tiempo de agotamiento
- Comportamiento de clientes

✅ **Visualizaciones**: 5 gráficos automáticos  
✅ **Cruce de Información**: 12 tipos de cruces MongoDB ↔ Redis  

---

## 👥 Equipo

- **Dataset**: Amazon E-commerce Products
- **Tecnologías**: Python 3.8+, MongoDB, Redis
- **Librerías**: pymongo, redis, pandas, matplotlib, seaborn

---

## 📝 Notas

- El simulador genera eventos aleatorios pero realistas
- Los tiempos de agotamiento se calculan desde el inicio de la simulación
- El análisis de pérdidas incluye:
  - `stock_out`: Sin stock disponible
  - `partial_checkout`: Compra parcial (stock insuficiente)
- Las visualizaciones se actualizan cada vez que ejecutas `main.py`

---

## 🎓 Documentación Adicional

- [`CRUCES_DE_INFORMACION.md`](CRUCES_DE_INFORMACION.md): Explicación detallada de cruces
- [`CYBERDAY_ETL.md`](CYBERDAY_ETL.md): Arquitectura del sistema
- [`SUMMARY.py`](SUMMARY.py): Script de resumen estadístico

---

¡Listo para simular tu Cyber Day! 🚀
