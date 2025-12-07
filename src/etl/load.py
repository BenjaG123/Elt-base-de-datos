"""
Módulo LOAD: Persistencia de datos transformados en bases de datos.

Este módulo implementa la fase L (Load) del proceso ETL, realizando:
- Persistencia de productos en MongoDB (catálogo)
- Persistencia de eventos de carrito en Redis (tiempo real)
- Guardado de datasets procesados en CSV (auditoría)
- Validación de datos antes de la carga
- Gestión de conexiones y manejo de errores

Destinos de datos:
- MongoDB: Catálogo de productos con inventario
- Redis: Eventos de carritos agrupados por sesión
- CSV: Backup de datos procesados

Autor: ETL Team
Fecha: 2025
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_CSV, get_mongo_connection, get_redis_connection
from src.etl.transform import transform_all
from src.utils import safe_float_conversion, safe_int_conversion, save_dataframe_to_csv

# ========================================================================
# CONSTANTES DE NEGOCIO
# ========================================================================

# Stock inicial para productos nuevos
DEFAULT_STOCK = 5

# Ventas iniciales para nuevos productos
DEFAULT_SALES = 0


# ========================================================================
# FUNCIONES DE CARGA PRINCIPALES
# ========================================================================


def load_products_to_mongodb(df: pd.DataFrame, recreate: bool = True) -> bool:
    """
    Carga productos transformados a MongoDB.

    Args:
        df: DataFrame con productos transformados
        recreate: Si True, limpia la colección antes de cargar

    Returns:
        True si la carga fue exitosa, False en caso contrario
    """
    if df is None or df.empty:
        print("[LOAD] No hay datos para cargar a MongoDB")
        return False

    client = None
    try:
        # Establecer conexión con MongoDB
        client, _, collection = get_mongo_connection()
        if collection is None:
            return False

        # Limpiar colección existente si se solicita
        if recreate:
            collection.delete_many({})
            print("[LOAD] Coleccion MongoDB limpiada")

        # Convertir DataFrame a documentos MongoDB usando iteración eficiente
        # Nota: to_dict('records') es más eficiente que iterrows()
        products = []
        for record in df.to_dict('records'):
            doc = {
                "product_id": record.get("product_id"),
                "product_name": record.get("product_name"),
                "category": record.get("category"),
                "actual_price": safe_float_conversion(record.get("actual_price")),
                "discounted_price": safe_float_conversion(record.get("discounted_price")),
                "discount_percentage": safe_float_conversion(record.get("discount_percentage")),
                "rating": safe_float_conversion(record.get("rating")),
                "rating_count": safe_int_conversion(record.get("rating_count")),
                "about_product": record.get("about_product", ""),
                # Campos de negocio para el inventario
                "stock": DEFAULT_STOCK,
                "total_sales": DEFAULT_SALES,
                "created_at": datetime.now(timezone.utc),
            }
            products.append(doc)

        # Inserción masiva (más eficiente que inserts individuales)
        # ordered=False permite continuar si algún documento falla
        insert_result = collection.insert_many(products, ordered=False)
        print(
            f"[LOAD] {len(insert_result.inserted_ids)} "
            f"productos cargados a MongoDB"
        )

        # Guardar copia en CSV para auditoría
        save_dataframe_to_csv(df, Path(PROCESSED_CSV).parent, "amazon_processed.csv")

        return True

    except Exception as e:
        print(f"[LOAD] Error cargando a MongoDB: {e}")
        return False

    finally:
        # Asegurar cierre de conexión incluso si hay error
        if client is not None:
            client.close()


def load_carts_to_redis(df: pd.DataFrame) -> bool:
    """
    Carga eventos de carrito agrupados por sesión a Redis.

    Args:
        df: DataFrame con eventos de carrito transformados

    Returns:
        True si la carga fue exitosa, False en caso contrario
    """
    if df is None or df.empty:
        print("[LOAD] No hay datos para cargar a Redis")
        return False

    redis_client = None
    try:
        # Establecer conexión con Redis
        redis_client = get_redis_connection()
        if redis_client is None:
            return False

        # Limpiar base de datos Redis existente
        redis_client.flushdb()
        print("[LOAD] Redis limpiado")

        # Agrupar eventos por carrito usando iteración eficiente
        # Estructura: {cart_id: {customer_id, events[], total_revenue, lost_revenue}}
        carts = {}
        for record in df.to_dict('records'):
            cart_id = record["cart_id"]

            # Inicializar carrito si es la primera vez
            if cart_id not in carts:
                carts[cart_id] = {
                    "customer_id": record["customer_id"],
                    "events": [],
                    "total_revenue": 0,
                    "lost_revenue": 0,
                }

            # Crear evento con datos del registro
            event = {
                "event_time": str(record["event_time"]),
                "event_type": record["event_type"],
                "product_id": record["product_id"],
                "quantity": safe_int_conversion(record["quantity"]),
                "stock_before": safe_int_conversion(record["stock_before"]),
                "stock_after": safe_int_conversion(record["stock_after"]),
                "revenue": safe_float_conversion(record["revenue"]),
                "lost_revenue": safe_float_conversion(record["lost_revenue"]),
            }

            # Agregar evento y acumular métricas
            carts[cart_id]["events"].append(event)
            carts[cart_id]["total_revenue"] += safe_float_conversion(record["revenue"])
            carts[cart_id]["lost_revenue"] += safe_float_conversion(record["lost_revenue"])

        # Persistir carritos en Redis como hash keys
        # Formato: cart:{cart_id} -> {customer_id, events, total_revenue, lost_revenue}
        for cart_id, cart_data in carts.items():
            redis_client.hset(
                f"cart:{cart_id}",
                mapping={
                    "customer_id": cart_data["customer_id"],
                    "events": json.dumps(cart_data["events"]),
                    "total_revenue": cart_data["total_revenue"],
                    "lost_revenue": cart_data["lost_revenue"],
                    "loaded_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        print(f"[LOAD] {len(carts)} carritos cargados a Redis")

        # Guardar copia en CSV para auditoría
        save_dataframe_to_csv(df, Path(PROCESSED_CSV).parent, "carts_processed.csv")

        return True

    except Exception as e:
        print(f"[LOAD] Error cargando a Redis: {e}")
        return False

    finally:
        # Asegurar cierre de conexión incluso si hay error
        if redis_client is not None:
            redis_client.close()


# ========================================================================
# FUNCIÓN PRINCIPAL DE ORQUESTACIÓN
# ========================================================================


def load_all(amazon_df: pd.DataFrame, cart_df: pd.DataFrame) -> bool:
    """
    Ejecuta la etapa LOAD completa del pipeline ETL.

    Carga datos transformados a:
    - MongoDB: Catálogo de productos
    - Redis: Eventos de carritos
    - CSV: Copias de auditoría

    Args:
        amazon_df: DataFrame con productos transformados
        cart_df: DataFrame con eventos de carrito transformados

    Returns:
        True si ambas cargas fueron exitosas, False en caso contrario
    """
    print("\n[LOAD] Iniciando carga de datos...\n")

    # Validar datos de entrada
    if amazon_df is None or amazon_df.empty:
        print("[LOAD] Error: se requiere el dataframe de productos de Amazon.")
        return False

    if cart_df is None or cart_df.empty:
        print("[LOAD] Error: se requiere el dataframe de eventos de carrito.")
        return False

    # Ejecutar cargas en paralelo lógico (independientes entre sí)
    mongo_ok = load_products_to_mongodb(amazon_df)
    redis_ok = load_carts_to_redis(cart_df)

    # Validar que ambas cargas fueron exitosas
    if mongo_ok and redis_ok:
        print("\n[LOAD] Todas las cargas completadas exitosamente")
    else:
        print("\n[LOAD] Advertencia: Algunas cargas fallaron")
        if not mongo_ok:
            print("  - MongoDB: FALLIDO")
        if not redis_ok:
            print("  - Redis: FALLIDO")

    return mongo_ok and redis_ok


def main():
    """Ejecuta el módulo LOAD de manera independiente."""
    print("[LOAD] Obteniendo datos transformados...")
    transform_result = transform_all()
    if transform_result is None:
        print("[LOAD] Error: no se pudieron obtener los datos transformados.")
        sys.exit(1)

    products_df, carts_df = transform_result
    load_all(products_df, carts_df)


if __name__ == "__main__":
    main()