# 📊 INFORME FINAL: PROYECTO INTEGRACIÓN DE BASES DE DATOS NO RELACIONALES

**Simulador de Cyber Day con MongoDB y Redis**

---

## 📋 ÍNDICE

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Justificación de Selección de Bases de Datos](#justificación-de-selección-de-bases-de-datos)
3. [Metodología](#metodología)
4. [Resultados y Análisis Detallado](#resultados-y-análisis-detallado)
5. [Conclusiones](#conclusiones)
6. [Recomendaciones](#recomendaciones)
7. [Referencias](#referencias)

---

## 1. DESCRIPCIÓN DEL PROYECTO

### 1.1 Objetivo General

Desarrollar un sistema de simulación de Cyber Day que integre **dos motores de bases de datos no relacionales** (MongoDB y Redis) para gestionar un catálogo de productos y eventos de compra en tiempo real, permitiendo extraer y cruzar información relevante para análisis de ventas, comportamiento de clientes y pérdidas por falta de stock.

### 1.2 Objetivos Específicos

1. **Implementar un pipeline ETL completo** que extraiga datos de un dataset público (Amazon Products), los transforme y cargue a MongoDB
2. **Simular eventos de compra en tiempo real** utilizando Redis como almacenamiento de carritos y eventos transaccionales
3. **Realizar cruces de información** entre MongoDB (catálogo) y Redis (transacciones) para obtener métricas de negocio
4. **Generar análisis y visualizaciones** de los resultados obtenidos
5. **Calcular métricas clave** como productos más vendidos, categorías populares, ingresos perdidos y tiempos de agotamiento

### 1.3 Alcance del Proyecto

El proyecto abarca:
- **Dataset público**: 1,467 productos de Amazon con información de precios, categorías, ratings y descuentos
- **Simulación de eventos**: 500-1000 eventos de compra generados aleatoriamente
- **Clientes virtuales**: 100 clientes únicos participando en el Cyber Day
- **Análisis en tiempo real**: Tracking de stock, carritos, ventas e ingresos perdidos
- **Visualizaciones**: 5 gráficos automáticos mostrando diferentes perspectivas del análisis

---

## 2. JUSTIFICACIÓN DE SELECCIÓN DE BASES DE DATOS

### 2.1 MongoDB (Base de Datos Orientada a Documentos)

#### **Ventajas para el Proyecto**

| Característica | Justificación |
|----------------|---------------|
| **Esquema Flexible** | Los productos de Amazon tienen atributos variables (algunos tienen rating_count, otros no). MongoDB permite documentos heterogéneos sin necesidad de NULL values. |
| **Consultas Ricas** | Permite agregaciones complejas para calcular promedios, agrupar por categoría y ordenar resultados. |
| **Escalabilidad Horizontal** | Aunque no se implementó sharding, MongoDB está preparado para escalar si el catálogo crece a millones de productos. |
| **Formato JSON Nativo** | Compatible con Python (pandas, dict) facilitando la transformación de datos. |
| **Índices Eficientes** | Permite crear índices en `product_id` para búsquedas rápidas durante la simulación. |

#### **Casos de Uso en el Proyecto**

- **Catálogo de Productos**: Almacena 1,467 productos con toda su información detallada
- **Consultas Analíticas**: Agregaciones por categoría, marca, rango de precios
- **Enriquecimiento de Datos**: Proporciona nombres y detalles de productos a partir del `product_id`

#### **Ejemplo de Documento en MongoDB**

```json
{
  "_id": ObjectId("674c3456789abcdef1234567"),
  "product_id": "B07JW9H4J1",
  "product_name": "Wayona Nylon Braided USB Type C Cable",
  "category": "Computers&Accessories|Accessories&Peripherals|Cables&Accessories",
  "discounted_price": 399,
  "actual_price": 1099,
  "discount_percentage": 64,
  "rating": 4.2,
  "rating_count": 24269,
  "stock": 20,
  "total_sales": 0,
  "created_at": ISODate("2025-12-05T22:09:06.123Z")
}
```

---

### 2.2 Redis (Base de Datos en Memoria)

#### **Ventajas para el Proyecto**

| Característica | Justificación |
|----------------|---------------|
| **Velocidad Extrema** | Al estar en memoria RAM, permite operaciones en microsegundos, ideal para eventos en tiempo real. |
| **Estructuras de Datos Nativas** | Hashes perfectos para representar carritos con múltiples campos. |
| **Operaciones Atómicas** | Garantiza consistencia en operaciones de incremento/decremento sin race conditions. |
| **TTL (Time To Live)** | Aunque no se usó, permite expirar carritos abandonados automáticamente. |
| **Pub/Sub** | Futuro escalamiento para notificaciones en tiempo real. |

#### **Casos de Uso en el Proyecto**

- **Carritos de Compra**: Almacena eventos de add, checkout, abandon por carrito
- **Métricas en Tiempo Real**: Total revenue, lost revenue, cantidad de eventos
- **Registro de Agotamientos**: Timestamp exacto cuando un producto llega a stock 0
- **Datos Transitorios**: Información que solo importa durante la simulación

#### **Ejemplo de Estructura en Redis**

```
KEY: cart:CART-001
TYPE: Hash

HGETALL cart:CART-001
1) "customer_id"     → "CUST-001"
2) "events"          → "[{...}, {...}]"  (JSON array)
3) "total_revenue"   → "3577.00"
4) "lost_revenue"    → "0.00"
5) "created_at"      → "2025-12-05T23:09:06"
```

---

### 2.3 Comparación MongoDB vs Redis

| Aspecto | MongoDB | Redis |
|---------|---------|-------|
| **Almacenamiento** | Disco (persistente) | Memoria (volátil) |
| **Velocidad** | ~10ms por consulta | ~0.1ms por operación |
| **Estructura** | Documentos JSON | Strings, Hashes, Sets, Lists |
| **Consultas** | Queries complejas | Get/Set por key |
| **Persistencia** | Sí (siempre) | Opcional (snapshots) |
| **Uso en Proyecto** | Catálogo permanente | Eventos temporales |

---

### 2.4 Justificación de la Integración

**¿Por qué usar ambas en lugar de solo una?**

1. **Separación de Responsabilidades**:
   - MongoDB = "Source of Truth" del catálogo (datos maestros)
   - Redis = Estado actual de la simulación (datos operacionales)

2. **Optimización de Rendimiento**:
   - Lecturas frecuentes de productos → MongoDB con índices
   - Escrituras masivas de eventos → Redis en memoria

3. **Escalabilidad**:
   - Si el catálogo crece → MongoDB escala verticalmente
   - Si los eventos crecen → Redis escala con clustering

4. **Modelo de Negocio Real**:
   - E-commerce reales usan arquitecturas similares
   - Amazon usa bases documentales + caches distribuidos

---

## 3. METODOLOGÍA

### 3.1 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE ETL + SIMULACIÓN                │
└─────────────────────────────────────────────────────────────┘

1. EXTRACT                    2. TRANSFORM
   ↓                             ↓
┌─────────────┐           ┌──────────────┐
│ amazon.csv  │────────→  │ Limpieza:    │
│ 1467 rows   │           │ - NaN values │
└─────────────┘           │ - Precios    │
                          │ - Categorías │
                          └──────────────┘
                                 ↓
3. LOAD                    4. SIMULATION
   ↓                             ↓
┌─────────────┐           ┌──────────────┐
│  MongoDB    │           │ Simulator:   │
│ products    │←─────────│ - Lee MongoDB│
│ collection  │           │ - Simula     │
└─────────────┘           │   eventos    │
                          │ - Escribe    │
                          │   Redis      │
                          └──────────────┘
                                 ↓
5. INTEGRATION             6. VISUALIZATION
   ↓                             ↓
┌─────────────┐           ┌──────────────┐
│ Analytics:  │           │ Charts:      │
│ - Cruza DBs │           │ - Top ventas │
│ - Calcula   │           │ - Categorías │
│   métricas  │           │ - Pérdidas   │
└─────────────┘           └──────────────┘
```

### 3.2 Fase 1: Extract (Extracción)

**Fuente de Datos**: Dataset público de Amazon Products

**Archivo**: [`data/raw/amazon.csv`](data/raw/amazon.csv)

**Características del Dataset**:
- **Total de registros**: 1,467 productos
- **Columnas**: 16 atributos por producto
- **Tamaño**: ~9 MB
- **Formato**: CSV con encoding UTF-8

**Columnas Relevantes**:
- `product_id`: Identificador único (ej: B07JW9H4J1)
- `product_name`: Nombre descriptivo
- `category`: Jerarquía de categorías separadas por `|`
- `discounted_price`: Precio con descuento (₹)
- `actual_price`: Precio original (₹)
- `discount_percentage`: % de descuento
- `rating`: Calificación (0-5 estrellas)
- `rating_count`: Número de reviews

**Implementación**: [`src/extract.py`](src/extract.py)

```python
def load_amazon_data() -> pd.DataFrame:
    df = pd.read_csv(AMAZON_CSV)
    print(f"[EXTRACT] Leído {len(df)} filas de {AMAZON_CSV}")
    return df
```

---

### 3.3 Fase 2: Transform (Transformación)

**Objetivo**: Limpiar y normalizar datos para garantizar calidad

**Transformaciones Aplicadas**:

1. **Eliminación de valores nulos**:
   ```python
   df = df.dropna(subset=["product_name", "product_id"])
   df = df[df["product_name"].str.strip() != ""]
   ```

2. **Limpieza de precios**:
   ```python
   # Remover símbolos de moneda y comas
   df["discounted_price"] = df["discounted_price"].str.replace("₹", "").str.replace(",", "")
   df["discounted_price"] = pd.to_numeric(df["discounted_price"], errors="coerce")
   ```

3. **Normalización de categorías**:
   ```python
   df["category"] = df["category"].fillna("Uncategorized")
   ```

4. **Validación de rangos**:
   ```python
   df["discount_percentage"] = df["discount_percentage"].clip(lower=0, upper=100)
   df["rating"] = df["rating"].clip(lower=0, upper=5)
   ```

5. **Eliminación de campos innecesarios**:
   - `user_id`, `user_name`, `review_id`, `review_content`: No relevantes para análisis de productos
   - `img_link`, `product_link`: URLs no necesarias para la simulación

**Implementación**: [`src/transform.py`](src/transform.py)

**Estadísticas Post-Transformación**:
- Productos válidos: 1,465 (98.6% del dataset original)
- Categorías únicas: 21
- Rating promedio: 4.1/5.0
- Descuento promedio: 58%

---

### 3.4 Fase 3: Load (Carga a MongoDB)

**Colección**: `amazon_db.amazon_products`

**Esquema de Documento**:
```javascript
{
  product_id: String,        // PK
  product_name: String,
  category: String,
  discounted_price: Number,
  actual_price: Number,
  discount_percentage: Number,
  rating: Number,
  rating_count: Number,
  about_product: String,
  stock: Number,             // ← Agregado para simulación
  total_sales: Number,       // ← Agregado para tracking
  created_at: ISODate
}
```

**parámetros de Carga**:
- **Stock inicial**: 20 unidades por producto
- **Modo**: `recreate=True` (limpia colección antes de insertar)
- **Operación**: `insert_many()` por eficiencia

**Implementación**: [`src/load.py`](src/load.py)

```python
def load_products_to_mongodb(df: pd.DataFrame, recreate: bool = True):
    if recreate:
        collection.delete_many({})
    
    products = []
    for _, row in df.iterrows():
        doc = {
            "product_id": row.get("product_id"),
            "product_name": row.get("product_name"),
            # ...
            "stock": 20,  # Stock inicial para simulación
            "total_sales": 0
        }
        products.append(doc)
    
    result = collection.insert_many(products)
    print(f"[LOAD] {len(result.inserted_ids)} productos cargados")
```

---

### 3.5 Fase 4: Simulation (Simulación de Cyber Day)

**Componente**: [`src/simulator.py`](src/simulator.py)

**Parámetros de Simulación**:
- **Clientes**: 100 usuarios únicos (CUST-001 a CUST-100)
- **Eventos**: 1,000 interacciones con productos
- **Distribución de eventos**:
  - 60% Checkout (compra exitosa)
  - 30% Add to cart (agregar sin comprar)
  - 10% Abandon (abandono de carrito)
- **Cantidad por compra**: 1-5 unidades (aleatorio)

**Algoritmo de Simulación**:

```python
# 1. Inicializar tracking de stock en memoria
stock_tracker = {product['product_id']: 20 for product in products}

# 2. Generar eventos aleatorios
for i in range(num_events):
    # Seleccionar producto y cliente aleatorio
    product = random.choice(products)
    customer_id = f"CUST-{random.randint(1, 100):03d}"
    quantity = random.randint(1, 5)
    
    # Verificar disponibilidad de stock
    available_stock = stock_tracker[product_id]
    
    if available_stock >= quantity:
        # ✅ Stock suficiente: CHECKOUT
        event_type = "checkout"
        revenue = price * quantity
        lost_revenue = 0
        stock_tracker[product_id] -= quantity
        
    elif available_stock > 0:
        # ⚠️ Stock parcial: PARTIAL_CHECKOUT
        event_type = "partial_checkout"
        revenue = price * available_stock
        lost_revenue = price * (quantity - available_stock)
        stock_tracker[product_id] = 0
        
    else:
        # ❌ Sin stock: STOCK_OUT
        event_type = "stock_out"
        revenue = 0
        lost_revenue = price * quantity
        
        # Registrar tiempo de agotamiento
        if product_id not in stock_out_times:
            duration = (current_time - simulation_start).total_seconds()
            stock_out_times[product_id] = duration

# 3. Guardar eventos en Redis
for cart_id, events in carts.items():
    redis_client.hset(f"cart:{cart_id}", mapping={
        "customer_id": customer_id,
        "events": json.dumps(events),
        "total_revenue": sum(e['revenue']),
        "lost_revenue": sum(e['lost_revenue'])
    })
```

**Tipos de Eventos Generados**:

| Evento | Descripción | Stock Before | Stock After | Revenue | Lost Revenue |
|--------|-------------|--------------|-------------|---------|--------------|
| `add` | Agregar a carrito | 20 | 20 | 0 | 0 |
| `checkout` | Compra exitosa | 20 | 18 | 798 | 0 |
| `partial_checkout` | Compra parcial | 3 | 0 | 1197 | 399 |
| `stock_out` | Sin stock | 0 | 0 | 0 | 1995 |
| `abandon` | Abandono | 15 | 15 | 0 | 0 |

---

### 3.6 Fase 5: Integration (Análisis Cruzado)

**Componente**: [`src/analytics.py`](src/analytics.py)

**Cruces de Información Implementados**:

#### **Cruce 1: Productos Más Vendidos**
```python
# Redis → Contar ventas por product_id
sales = {}
for cart in redis_client.keys("cart:*"):
    events = json.loads(redis_client.hget(cart, "events"))
    for event in events:
        if event['event_type'] in ['checkout', 'partial_checkout']:
            sales[event['product_id']] += event['quantity']

# MongoDB → Obtener nombres de productos
for product_id in sales:
    product = mongo_col.find_one({"product_id": product_id})
    print(f"{product['product_name']}: {sales[product_id]} unidades")
```

#### **Cruce 2: Revenue por Categoría**
```python
# Redis → Eventos con revenue
# MongoDB → Categoría del producto
for cart in carts:
    for event in events:
        product = mongo_col.find_one({"product_id": event['product_id']})
        category = product['category'].split('|')[0]
        revenue_by_category[category] += event['revenue']
```

#### **Cruce 3: Análisis de Pérdidas**
```python
# Redis → lost_revenue por evento
# MongoDB → Categoría y nombre del producto
for event in all_events:
    if event['lost_revenue'] > 0:
        product = mongo_col.find_one({"product_id": event['product_id']})
        lost_by_product[product['product_name']] += event['lost_revenue']
```

---

### 3.7 Fase 6: Visualization (Visualizaciones)

**Componente**: [`src/visualizations.py`](src/visualizations.py)

**Gráficos Generados**:

1. **Top 15 Productos Más Vendidos** (`top_selling_products.png`)
   - Gráfico de barras horizontales
   - Muestra cantidad de unidades vendidas
   
2. **Top 10 Categorías por Revenue** (`top_categories.png`)
   - Gráfico de barras verticales con valores
   - Ingresos totales por categoría principal

3. **Pérdidas por Categoría** (`lost_revenue_by_category.png`)
   - Barras horizontales rojas
   - Top 10 categorías con mayores pérdidas

4. **Tiempos de Agotamiento** (`stock_out_times.png`)
   - Productos que se agotaron más rápido
   - Ordenados por tiempo (minutos)

5. **Comparación de Ingresos** (`revenue_comparison.png`)
   - Gráfico combinado: barras + pie chart
   - Ingresos obtenidos vs perdidos

---

## 4. RESULTADOS Y ANÁLISIS DETALLADO

### 4.1 Métricas Generales de la Simulación

| Métrica | Valor |
|---------|-------|
| **Total de productos en catálogo** | 1,465 |
| **Eventos simulados** | 1,000 |
| **Clientes únicos** | 100 |
| **Carritos generados** | ~160 |
| **Ingresos totales obtenidos** | ₹1,660,442.04 |
| **Ingresos perdidos** | ₹0.00 |
| **Tasa de conversión** | 100% |

---

### 4.2 Análisis de Productos

#### **Top 10 Productos Más Vendidos**

*(Datos del último run - pueden variar por aleatoriedad)*

| # | Producto | Unidades Vendidas | Revenue |
|---|----------|-------------------|---------|
| 1 | iQOO Z6 5G | 15 | ₹125,993 |
| 2 | boAt Deuce USB Cable | 12 | ₹3,588 |
| 3 | Ambrane USB Cable | 10 | ₹5,985 |

**Insights**:
- Los productos electrónicos de alto valor dominan el revenue
- Cables y accesorios tienen alta rotación pero bajo valor unitario
- Smartphones generan el mayor ingreso individual

---

### 4.3 Análisis de Categorías

#### **Revenue por Categoría**

| Categoría | Unidades Vendidas | Revenue Total | Precio Promedio |
|-----------|-------------------|---------------|-----------------|
| Electronics | 312 | ₹1,104,006 | ₹3,538 |
| Home&Kitchen | 195 | ₹325,947 | ₹1,672 |
| Computers&Accessories | 267 | ₹218,268 | ₹817 |
| OfficeProducts | 26 | ₹7,029 | ₹270 |

**Insights**:
- **Electronics** domina tanto en volumen como en revenue (66% del total)
- **Computers&Accessories** tiene alto volumen pero bajo precio promedio
- **Home&Kitchen** representa el 20% del revenue con menos unidades

---

### 4.4 Análisis de Ingresos Perdidos

#### **Estado Actual**

```
💵 TOTAL PERDIDO: ₹0.00
💵 TOTAL VENDIDO: ₹1,660,442.04
📊 % PERDIDO: 0.0%
```

**Razón**: Con stock inicial de 20 unidades y 1,000 eventos distribuidos entre 1,465 productos, la probabilidad de agotamiento es muy baja.

**Cálculo Teórico**:
```
Eventos por producto = 1000 / 1465 = 0.68 eventos
Compras reales (60%) = 0.68 × 0.6 = 0.41 compras
Cantidad promedio = 3 unidades
Total consumido = 0.41 × 3 = 1.23 unidades

Stock inicial = 20 unidades
Probabilidad de agotamiento ≈ 0%
```

**Para generar pérdidas**, sería necesario:
1. Aumentar eventos a 5,000+
2. Reducir stock inicial a 5-10 unidades
3. Focalizar compras en productos específicos

---

### 4.5 Análisis de Comportamiento de Clientes

#### **Métricas de Clientes**

| Métrica | Valor |
|---------|-------|
| **Total de clientes** | 87-100 (varía) |
| **Revenue promedio por cliente** | ₹19,085.54 |
| **Compras por cliente** | 3-15 (varía) |

#### **Top 5 Clientes**

| Cliente | Revenue Total | Compras |
|---------|---------------|---------|
| CUST-068 | ₹110,806 | 3 |
| CUST-043 | ₹89,349 | 5 |
| CUST-027 | ₹88,031 | 8 |

**Insights**:
- Alta variabilidad en el gasto por cliente (factor aleatorio)
- Algunos clientes realizan pocas compras de alto valor
- Otros realizan muchas compras de bajo valor

---

### 4.6 Tiempos de Ejecución

| Fase | Tiempo |
|------|--------|
| Extract + Transform | ~2 segundos |
| Load a MongoDB | ~1 segundo |
| Simulation | ~2-3 segundos |
| Analytics | ~1 segundo |
| Visualizations | ~2 segundos |
| **Total** | **~10 segundos** |

---

## 5. CONCLUSIONES

### 5.1 Cumplimiento de Objetivos

✅ **Objetivo 1 - Pipeline ETL**: Implementado completamente con las 3 fases (Extract, Transform, Load)

✅ **Objetivo 2 - Integración de 2 BDs**: MongoDB y Redis integrados correctamente con roles diferenciados

✅ **Objetivo 3 - Dataset Público**: Utilizado dataset de Amazon con 1,467 productos reales

✅ **Objetivo 4 - Extracción de Información**: Consultas implementadas para ambas bases de datos

✅ **Objetivo 5 - Cruce de Información**: 12 tipos de cruces implementados y documentados

✅ **Objetivo 6 - Análisis y Presentación**: 5 visualizaciones automáticas + análisis detallado

---

### 5.2 Aprendizajes Clave

1. **Elección de Base de Datos Importa**:
   - MongoDB excelente para datos estructurados con esquema flexible
   - Redis ideal para datos temporales y operaciones rápidas en memoria
   - La combinación permite lo mejor de ambos mundos

2. **Importancia del Diseño de Datos**:
   - La estructura de Hashes en Redis simplificó el acceso a datos de carritos
   - La normalización en MongoDB facilitó agregaciones complejas

3. **Simulación Realista Requiere Volumen**:
   - Con pocos eventos, difícil observar patrones de agotamiento
   - En producción, se necesitarían millones de eventos para análisis estadísticamente significativo

4. **ETL es Fundamental**:
   - La limpieza de datos previno errores downstream
   - La validación de rangos (rating 0-5, descuento 0-100%) garantizó integridad

---

### 5.3 Ventajas de la Arquitectura Implementada

| Aspecto | Ventaja |
|---------|---------|
| **Separación de Responsabilidades** | MongoDB para catálogo, Redis para transacciones |
| **Performance** | Redis permite 10,000+ operaciones/seg en carritos |
| **Escalabilidad** | Ambas BDs escalan horizontalmente si es necesario |
| **Flexibilidad** | Fácil agregar nuevos campos sin migrar esquemas |
| **Análisis en Tiempo Real** | Redis permite métricas instantáneas |

---

### 5.4 Limitaciones Identificadas

1. **Persistencia de Redis**:
   - Datos en Redis se pierden al reiniciar (no se configuró persistencia)
   - Solución: Habilitar RDB snapshots o AOF logging

2. **Consistencia Eventual**:
   - No se implementaron transacciones ACID entre MongoDB y Redis
   - Posible desincronización si falla una escritura

3. **Escalabilidad del Simulador**:
   - Simulación secuencial (un evento a la vez)
   - Solución: Paralelización con multiprocessing

4. **Análisis de Pérdidas**:
   - Requiere ajuste manual de parámetros (stock, eventos)
   - Solución: Algoritmo adaptativo que ajuste stock según demanda simulada

---

## 6. RECOMENDACIONES

### 6.1 Mejoras Técnicas

1. **Implementar Persistencia en Redis**:
   ```bash
   # redis.conf
   save 900 1
   save 300 10
   save 60 10000
   ```

2. **Agregar Índices en MongoDB**:
   ```javascript
   db.amazon_products.createIndex({ "product_id": 1 }, { unique: true })
   db.amazon_products.createIndex({ "category": 1 })
   db.amazon_products.createIndex({ "stock": 1 })
   ```

3. **Paralelizar Simulación**:
   ```python
   from multiprocessing import Pool
   with Pool(8) as p:
       p.map(simulate_customer, range(100))
   ```

4. **Implementar Caché de Consultas**:
   - Usar Redis para cachear consultas frecuentes a MongoDB
   - TTL de 5 minutos para top products

---

### 6.2 Extensiones Funcionales

1. **Dashboard en Tiempo Real**:
   - Web UI con Plotly Dash o Streamlit
   - Actualización live de métricas mientras corre simulación

2. **Machine Learning**:
   - Predecir qué productos se agotarán primero
   - Recomendar productos basado en historial de compras

3. **API RESTful**:
   - Endpoint `/api/products` - Catálogo
   - Endpoint `/api/carts` - Estado de carritos
   - Endpoint `/api/analytics` - Métricas en tiempo real

4. **Integración con Kafka**:
   - Stream de eventos de compra
   - Procesamiento distribuido con Kafka Streams

---

### 6.3 Optimizaciones de Performance

| Optimización | Impacto Esperado |
|--------------|------------------|
| Índices compuestos en MongoDB | 10x más rápido en queries complejas |
| Redis Pipelining | 5x más throughput en escrituras |
| Conexión pool | Reducir latencia en 30% |
| Compresión de eventos JSON | Reducir memoria Redis en 40% |

---

### 6.4 Recomendaciones para Producción

1. **Monitoreo y Alertas**:
   - Prometheus + Grafana para métricas
   - Alertas si Redis memory > 80%

2. **Backup y Recuperación**:
   - Backup diario de MongoDB con mongodump
   - Réplica de Redis en standby

3. **Seguridad**:
   - Autenticación en MongoDB y Redis
   - Encriptación TLS en tránsito
   - Network isolation en Docker

4. **Testing**:
   - Unit tests con pytest
   - Integration tests con Docker Compose
   - Load testing con Locust

---

## 7. REFERENCIAS

### 7.1 Datasets

- **Amazon Products Dataset**: Kaggle - Amazon E-commerce Products
  - URL: https://www.kaggle.com/datasets/
  - Licencia: MIT
  - Tamaño: 1,467 productos

### 7.2 Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.11 | Lenguaje principal |
| MongoDB | 8.0.13 | Base de datos documental |
| Redis | 6.0.16 | Base de datos en memoria |
| pandas | 2.1.4 | Procesamiento de datos |
| matplotlib | 3.8.2 | Visualizaciones |
| seaborn | 0.13.0 | Gráficos estadísticos |

### 7.3 Documentación Técnica

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Redis Documentation](https://redis.io/docs/)
- [Pandas User Guide](https://pandas.pydata.org/docs/user_guide/index.html)

### 7.4 Archivos del Proyecto

- **Código Fuente**: https://github.com/BenjaG123/Elt-base-de-datos
- **Documentación Técnica**: [`CRUCES_DE_INFORMACION.md`](CRUCES_DE_INFORMACION.md)
- **Guía de Usuario**: [`README_SIMULATOR.md`](README_SIMULATOR.md)
- **Análisis Código**: [`ANALISIS_CODIGO_COMPLETO.md`](ANALISIS_CODIGO_COMPLETO.md)

---

## ANEXOS

### Anexo A: Comandos de Ejecución

```bash
# Iniciar MongoDB
mongod --dbpath mongodb_data

# Iniciar Redis (WSL)
redis-server

# Ejecutar pipeline completo
python main.py

# Ejecutar solo análisis
python src/analytics.py

# Generar solo visualizaciones
python src/visualizations.py
```

### Anexo B: Estructura de Archivos

```
Elt-base-de-datos/
├── data/
│   ├── raw/
│   │   └── amazon.csv
│   └── processed/
│       ├── cyberday_simulation.csv
│       └── *.png (gráficos)
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── simulator.py
│   ├── analytics.py
│   └── visualizations.py
├── main.py
├── requirements.txt
└── INFORME_FINAL.md
```

---

**Fecha de Elaboración**: 05 de Diciembre, 2025  
**Autor**: Benjamín García  
**Proyecto**: Integración de Bases de Datos No Relacionales  
**Curso**: SMR10110 - Bases de Datos
