# 🔄 CRUCES DE INFORMACIÓN: MongoDB ↔ Redis

## Resumen Ejecutivo

El cruce de información ocurre en **3 momentos clave** del pipeline ETL:

```
MOMENTO 1: LOAD (Carga inicial)
MOMENTO 2: INTEGRATION (Sincronización en tiempo real)
MOMENTO 3: TRANSFORM (Análisis cruzado)
```

---

## 🌍 MOMENTO 1: LOAD (Carga Inicial)

### Estructura Paralela de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATOS DE ENTRADA                             │
│  flipkart_com-ecommerce_sample.csv     redis_cart_sim.csv      │
└──────────────┬─────────────────────────────────────┬────────────┘
               │                                     │
               ↓                                     ↓
        ┌─────────────────────┐            ┌──────────────────┐
        │   LOAD A MONGODB    │            │  LOAD A REDIS    │
        │  (Catálogo)         │            │ (Carritos)       │
        ├─────────────────────┤            ├──────────────────┤
        │ - uniq_id           │            │ - cart_id        │
        │ - product_name      │            │ - customer_id    │
        │ - pid (KEY)         │            │ - events[]       │
        │ - retail_price      │            │ - total_revenue  │
        │ - discounted_price  │            │ - lost_revenue   │
        │ - brand             │            │ - product_id     │
        │ - stock: 100        │            │ - quantity       │
        │ - total_sales: 0    │            │ - event_type     │
        └──────┬──────────────┘            └────────┬─────────┘
               │                                    │
               ↓                                    ↓
        ┌──────────────────────┐          ┌──────────────────┐
        │   MONGODB            │          │    REDIS         │
        │                      │          │                  │
        │ Collection:          │          │ Keys:            │
        │ "products"           │          │ "cart:CART-001"  │
        │                      │          │ "cart:CART-002"  │
        │ ~15,000 docs         │          │ "customer:CUST-01"
        └──────────────────────┘          └──────────────────┘

⚠️ PUNTO CRÍTICO DE CRUCE #1:
   - MongoDB: almacena CATÁLOGO (datos estáticos)
   - Redis: almacena ESTADO (datos en tiempo real)
   - El cruce ocurre cuando Redis referencia product_id de MongoDB
```

---

## ⚡ MOMENTO 2: INTEGRATION (Sincronización en Tiempo Real)

### El Gran Cruce: Integration Layer

```python
# FLUJO DE UN EVENTO DE CARRITO
┌─────────────────────────────────────────────────────────────────┐
│                    EVENTO: CART-001 agrega P-1001               │
├─────────────────────────────────────────────────────────────────┤

PASO 1: LECTURA EN REDIS
═══════════════════════════
redis_client.hgetall("cart:CART-001")
└─→ Retorna: {
      "customer_id": "CUST-01",
      "events": [...],
      "total_revenue": 0
    }

PASO 2: LOOKUP EN MONGODB
═════════════════════════
mongo_col.find_one({
    "pid": "P-1001"
})
└─→ Retorna: {
      "_id": ObjectId(...),
      "product_name": "Alisha Solid Women's Cycling Shorts",
      "discounted_price": 379,
      "stock": 120,           ← INFORMACIÓN CRÍTICA
      "total_sales": 5
    }

PASO 3: VALIDACIÓN
══════════════════
¿stock (120) >= cantidad_solicitada (1)?
✅ SÍ → Continuar
❌ NO → Rechazar y marcar como STOCK_OUT

PASO 4: UPDATE EN MONGODB
═════════════════════════
db.products.update_one(
    {"pid": "P-1001"},
    {
        "$inc": {"stock": -1},        ← REDUCE STOCK
        "$inc": {"total_sales": 1}    ← INCREMENTA CONTADOR
    }
)
MongoDB ANTES:  stock = 120, total_sales = 5
MongoDB DESPUÉS: stock = 119, total_sales = 6

PASO 5: UPDATE EN REDIS
═══════════════════════
redis_client.hset("cart:CART-001", {
    "events": [..., {
        "product_id": "P-1001",
        "product_name": "Alisha...",
        "product_price": 379,
        "quantity": 1,
        "event_type": "add"
    }],
    "total_revenue": 379  ← ACTUALIZADO
})

PASO 6: RESPUESTA AL USUARIO
════════════════════════════
{
  "status": "success",
  "message": "Producto agregado al carrito",
  "remaining_stock": 119,
  "cart_value": 379
}

└─→ FIN: MongoDB y Redis están SINCRONIZADOS ✅
```

### Diagrama de Interacción en Tiempo Real

```
USUARIO                REDIS              MONGODB
  │                     │                   │
  ├─ agrega P-1001 ──→  │                   │
  │                     │                   │
  │                  [Busca en ]────────────→ lookup: pid=P-1001
  │                  [carrito]←─────────────  ← retorna: stock=120
  │                     │                   │
  │                  [Valida]───────────────→ update: stock 120→119
  │                  [stock]←─────────────  ← confirma
  │                     │                   │
  │  ←─ success ────    │                   │
  │  remaining_stock    │                   │
  │  = 119             │                   │
  │                    │                   │
  ├─ checkout ───────→  │                   │
  │                  [Procesa]──────────────→ update: total_sales++
  │                  [orden]   ←────────────  ← confirma venta
  │                     │                   │
  │  ← order_id ───    │                   │
  │    ORD-CART-001    │                   │
  │                    │                   │
```

---

## 🔍 TIPOS DE CRUCES DE INFORMACIÓN

### Cruce Tipo 1: LOOKUP (MongoDB ← Redis)

**Cuándo**: Cuando hay un evento en carrito

**Qué se cruza**: `product_id` en Redis busca datos en MongoDB

```python
# Redis tiene:
{
  "cart_id": "CART-001",
  "events": [
    {
      "product_id": "P-1001",  ← Clave de búsqueda
      "quantity": 1
    }
  ]
}

# MongoDB consulta:
db.products.find_one({"pid": "P-1001"})

# MongoDB retorna:
{
  "product_name": "...",
  "discounted_price": 379,  ← Necesario para Redis
  "stock": 120              ← Necesario para validación
}

# Redis actualiza:
{
  "events": [
    {
      "product_id": "P-1001",
      "product_name": "...",      ← ENRIQUECIDO
      "product_price": 379,       ← ENRIQUECIDO
      "quantity": 1
    }
  ]
}
```

**Ejemplo en código** (`src/integration.py`):
```python
def enrich_carts_with_product_info():
    # 1. Obtener productos de MongoDB
    products = {}
    for doc in mongo_col.find({}, {"pid": 1, "product_name": 1}):
        products[doc["pid"]] = {
            "name": doc.get("product_name"),
            "price": doc.get("discounted_price")
        }
    
    # 2. Usar productos para enriquecer carritos en Redis
    cart_keys = redis_client.keys("cart:CART-*")
    for key in cart_keys:
        cart_data = redis_client.hgetall(key)
        events = json.loads(cart_data.get("events", "[]"))
        
        for event in events:
            product_id = event.get("product_id")
            if product_id in products:
                # CRUCE: Agregar info de MongoDB a Redis
                event["product_name"] = products[product_id]["name"]
                event["product_price"] = products[product_id]["price"]
```

---

### Cruce Tipo 2: STOCK SYNC (MongoDB ↔ Redis)

**Cuándo**: Cuando hay un evento `add` o `checkout`

**Qué se cruza**: Cantidad de stock se sincroniza en ambos sentidos

```
ESCENARIO:
┌──────────────────────────────────────────────────────┐
│  P-1001 tiene stock = 120 en MongoDB                 │
│  Usuario agrega 1 unidad al carrito                  │
└──────────────────────────────────────────────────────┘

CRUCE #1: ADD event
───────────────────
ANTES:
  MongoDB: P-1001.stock = 120
  Redis:   cart:CART-001 = {items: []}

PROCESO:
  1. Redis envía producto_id = P-1001
  2. MongoDB consulta: SELECT stock FROM products WHERE pid = P-1001
  3. MongoDB valida: 120 >= 1 ✅
  4. MongoDB actualiza: stock = 120 - 1 = 119
  5. Redis recibe confirmación y guarda:
     {
       "events": [{
         "product_id": "P-1001",
         "quantity": 1,
         "stock_available": 119
       }]
     }

DESPUÉS:
  MongoDB: P-1001.stock = 119
  Redis:   cart:CART-001 = {eventos con P-1001}
  
✅ SINCRONIZADO


CRUCE #2: CHECKOUT event
─────────────────────────
ANTES:
  MongoDB: P-1001.stock = 119, total_sales = 5
  Redis:   cart:CART-001.status = "active"

PROCESO:
  1. Redis envía: CHECKOUT event
  2. MongoDB valida: todos los items disponibles ✅
  3. MongoDB actualiza:
     - stock: 119 - 1 = 118 (definitivo)
     - total_sales: 5 + 1 = 6
     - Crea documento en "orders"
  4. Redis recibe confirmación y actualiza:
     {
       "status": "completed",
       "order_id": "ORD-CART-001"
     }

DESPUÉS:
  MongoDB: P-1001.stock = 118, total_sales = 6
  Redis:   cart:CART-001.status = "completed"
  
✅ SINCRONIZADO


CRUCE #3: ABANDON event
───────────────────────
ANTES:
  MongoDB: P-1001.stock = 118
  Redis:   cart:CART-001.status = "active"

PROCESO:
  1. Redis envía: ABANDON event
  2. MongoDB identifica items en carrito
  3. MongoDB libera stock (ROLLBACK):
     - stock: 118 + 1 = 119
  4. Redis marca como abandonado

DESPUÉS:
  MongoDB: P-1001.stock = 119 (stock LIBERADO)
  Redis:   cart:CART-001.status = "abandoned"
  
✅ SINCRONIZADO (Stock vuelve a disponibilidad)
```

---

### Cruce Tipo 3: ANALYTICS (Agregación)

**Cuándo**: Al final del pipeline (TRANSFORM)

**Qué se cruza**: Se combinan métricas de MongoDB + Redis

```python
# MongoDB proporciona (src/integration.py):
def get_product_performance_mongodb():
    pipeline = [
        {
            "$group": {
                "_id": "$brand",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$discounted_price"},
                "avg_discount": {"$avg": {"$subtract": [...]}}
            }
        }
    ]
    results = collection.aggregate(pipeline)
    
    return {
        "top_brands": results,
        "total_products": collection.count_documents({}),
        "timestamp": datetime.utcnow().isoformat()
    }

# Redis proporciona (src/integration.py):
def get_cart_analytics_redis():
    cart_keys = redis_client.keys("cart:CART-*")
    
    metrics = {
        "total_carts": len(cart_keys),
        "total_revenue": sum(...),
        "abandoned_carts": count(...),
        "checkout_events": count(...)
    }
    
    return metrics

# TRANSFORM cruza ambos (src/transform.py):
def transform_all():
    # Obtener datos de ambos lados
    mongo_metrics = get_product_performance_mongodb()
    redis_metrics = get_cart_analytics_redis()
    
    # CRUCE: Correlacionar datos
    combined_report = {
        "catalog": mongo_metrics["top_brands"],
        "sales": redis_metrics["checkout_events"],
        "revenue": redis_metrics["total_revenue"],
        "conversion_rate": (
            redis_metrics["checkout_events"] / mongo_metrics["total_products"]
        ),
        "abandonment_rate": (
            redis_metrics["abandoned_carts"] / redis_metrics["total_carts"]
        )
    }
    
    return combined_report
```

---

## 📊 Tabla de Cruces de Información

| Cruce | Origen | Destino | Datos Transferidos | Cuándo | Tipo |
|-------|--------|---------|-------------------|--------|------|
| **#1** | Redis | MongoDB | `product_id` | ADD event | Lookup |
| **#2** | MongoDB | Redis | `stock`, `price`, `name` | Validación | Enriquecimiento |
| **#3** | MongoDB | MongoDB | `stock` cantidad | Confirmación | Actualización |
| **#4** | Redis | MongoDB | `items[]`, `total_value` | CHECKOUT | Confirmación |
| **#5** | MongoDB | Redis | `order_id`, confirmación | CHECKOUT | Respuesta |
| **#6** | Redis | MongoDB | `product_id`, cantidad | ABANDON | Rollback |
| **#7** | MongoDB | MongoDB | `stock` liberado | ABANDON | Reversión |
| **#8** | MongoDB | TRANSFORM | Agregaciones, estadísticas | Final | Analytics |
| **#9** | Redis | TRANSFORM | Métricas de carritos | Final | Analytics |

---

## 🎯 Ejemplo Completo: Un Carrito Real

### Escenario: Cliente compra 2 productos

```
TIMELINE DETALLADO DEL CRUCE DE INFORMACIÓN
════════════════════════════════════════════

T=0s: ESTADO INICIAL
─────────────────────
MongoDB:
  P-1001: {stock: 100, total_sales: 0, price: 379}
  P-1002: {stock: 50,  total_sales: 0, price: 4999}

Redis:
  (vacío)


T=5s: CLIENTE AGREGA P-1001
──────────────────────────
REDIS INICIA:
  redis.hset("cart:CART-001", {...})
  └─→ {customer_id: "CUST-01", events: []}

CRUCE #1: Lookup en MongoDB
  redis → mongodb
  "¿Existe P-1001?" "¿Cuánto stock hay?"
  ← Retorna: {stock: 100, price: 379}

VALIDACIÓN:
  100 >= 1 ✅

CRUCE #2: Update en MongoDB
  mongodb.update({pid: "P-1001"}, {stock: 99})

CRUCE #3: Update en Redis
  redis.hset("cart:CART-001", "events", [
    {
      "product_id": "P-1001",
      "quantity": 1,
      "product_name": "Alisha...",
      "product_price": 379,
      "event_type": "add",
      "timestamp": "2025-05-05T10:00:00"
    }
  ])

ESTADO:
  MongoDB: P-1001.stock = 99
  Redis:   CART-001 has 1 item


T=10s: CLIENTE AGREGA P-1002
──────────────────────────
CRUCE #4: Lookup en MongoDB
  "¿Existe P-1002?" "¿Cuánto stock hay?"
  ← Retorna: {stock: 50, price: 4999}

VALIDACIÓN:
  50 >= 1 ✅

CRUCE #5: Update en MongoDB
  mongodb.update({pid: "P-1002"}, {stock: 49})

CRUCE #6: Update en Redis
  redis.hset("cart:CART-001", "events", [
    ... evento P-1001 ...
    ... evento P-1002 ... ← NUEVO
  ])

ESTADO:
  MongoDB: P-1001.stock = 99, P-1002.stock = 49
  Redis:   CART-001 has 2 items (P-1001, P-1002)


T=20s: CLIENTE HACE CHECKOUT
───────────────────────────
CRUCE #7: Validación Final en MongoDB
  Para cada item en carrito:
    "¿Stock disponible?" ✅
    "¿Validar precio?"   ✅

CRUCE #8: Commit en MongoDB (TRANSACCIÓN)
  UPDATE P-1001: stock 99 → 98, total_sales 0 → 1
  UPDATE P-1002: stock 49 → 48, total_sales 0 → 1
  INSERT order:
    {
      "order_id": "ORD-CART-001",
      "customer_id": "CUST-01",
      "items": [
        {"product_id": "P-1001", "qty": 1, "price": 379},
        {"product_id": "P-1002", "qty": 1, "price": 4999}
      ],
      "total": 5378
    }

CRUCE #9: Actualizar Redis
  redis.hset("cart:CART-001", {
    "status": "completed",
    "order_id": "ORD-CART-001",
    "total_revenue": 5378,
    "completed_at": "2025-05-05T10:00:20"
  })

ESTADO FINAL:
  MongoDB:
    - P-1001: stock = 98, total_sales = 1
    - P-1002: stock = 48, total_sales = 1
    - orders: 1 documento nuevo
  
  Redis:
    - CART-001: estado = "completed", total = 5378


T=30s: GENERAR REPORTES (TRANSFORM)
────────────────────────────────────
CRUCE #10: MongoDB proporciona
  - Total catálogo: 15000 productos
  - Total vendido: 2 items
  - Revenue potencial: ~$5M

CRUCE #11: Redis proporciona
  - Carritos activos: 0
  - Carritos completados: 1
  - Carritos abandonados: 0
  - Revenue actual: $5,378

CRUCE #12: Analytics combina
  {
    "catalog_size": 15000,
    "conversion_rate": 1/15000 = 0.0067%,
    "revenue": 5378,
    "avg_order_value": 5378,
    "customer_ltv": 5378
  }

REPORTE FINAL ✅
════════════════════════════════════════
MongoDB ← FUENTE DE VERDAD → Redis
  - Catálogo consistente
  - Stock sincronizado
  - Transacciones completadas
  - Métricas integradas
```

---

## 🔐 Garantías de Consistencia

### Problema: ¿Qué pasa si MongoDB falla?

```
Escenario de Error:
──────────────────
T=5s: Cliente agrega P-1001
  1. Redis guarda evento
  2. MongoDB BEGIN TRANSACTION
  3. MongoDB reduce stock
  4. MongoDB COMMIT ✅

✅ SEGURO: Si falla aquí, Redis y MongoDB están sincronizados


T=5s: Cliente agrega P-1001
  1. Redis guarda evento
  2. MongoDB BEGIN TRANSACTION
  3. MongoDB reduce stock
  4. MongoDB COMMIT ❌ FALLA

⚠️ INCONSISTENCIA:
  - Redis: P-1001 en carrito
  - MongoDB: P-1001 stock NO ACTUALIZADO
  
SOLUCIÓN:
  - Reintentar transaction
  - Mantener log de eventos
  - Usar idempotencia (mismo evento = mismo resultado)
```

### Implementación en Código

```python
def safe_add_to_cart(cart_id, product_id, quantity):
    """Agrega producto a carrito con garantía de consistencia."""
    
    # 1. Transacción en MongoDB
    session = client.start_session()
    try:
        with session.start_transaction():
            # Lookup
            product = db.products.find_one(
                {"pid": product_id},
                session=session
            )
            
            if not product or product["stock"] < quantity:
                raise Exception("Stock insuficiente")
            
            # Update
            db.products.update_one(
                {"pid": product_id},
                {"$inc": {"stock": -quantity}},
                session=session
            )
        
        # 2. Si MongoDB fue exitoso, actualizar Redis
        redis_client.hset(f"cart:{cart_id}", "events", ...)
        return {"status": "success"}
        
    except Exception as e:
        # Rollback automático en MongoDB
        print(f"Error, rollback: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        session.end_session()
```

---

## 📈 Resumen: Dónde Ocurren los Cruces

```
┌─────────────────────────────────────────────────────────────┐
│                   PIPELINE COMPLETO                         │
├─────────────────────────────────────────────────────────────┤

EXTRACT
├─ Lee Flipkart CSV
└─ Lee Redis Cart CSV
   (sin cruces aún)

      ↓ ↓

LOAD
├─ MongoDB: Catálogo de productos
├─ Redis: Carritos sin enriquecer
└─ ⚠️ CRUCE #1: Referencia de product_id

      ↓ ↓

INTEGRATION ← ⭐⭐⭐ CRUCES PRINCIPALES ⭐⭐⭐
├─ CRUCE #2-7: Sincronización stock
│  └─ ADD → Lookup MongoDB → Update MongoDB → Update Redis
│  └─ CHECKOUT → Validación MongoDB → Commit MongoDB → Update Redis
│  └─ ABANDON → Liberar stock MongoDB → Update Redis
│
├─ CRUCE #8-9: Enriquecimiento
│  └─ Redis busca nombres de productos en MongoDB
│
└─ CRUCE #10-11: Analytics
   └─ Agregar datos MongoDB + Redis

      ↓ ↓

TRANSFORM
├─ CRUCE #12: Combinar métricas
│  └─ KPIs de MongoDB (catálogo) + KPIs de Redis (ventas)
└─ Generar reportes inteligrados

      ↓ ↓

VISUALIZE
└─ Mostrar resultados

└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Conclusión

El cruce de información ocurre en **3 capas**:

1. **CARGA (LOAD)**: Datos paralelos que se referencian por `product_id`
2. **INTEGRACIÓN (INTEGRATION)**: Sincronización activa en tiempo real
3. **ANÁLISIS (TRANSFORM)**: Combinación de métricas para reportes

El código asegura que:
- ✅ MongoDB es la **fuente de verdad** (catálogo y stock)
- ✅ Redis es el **estado actual** (carritos activos)
- ✅ Ambos se sincronizan **en cada operación**
- ✅ Hay **rollback automático** en caso de error
