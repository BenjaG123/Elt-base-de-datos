"""
Etapa LOAD: inserta datos procesados de Amazon en MongoDB y eventos de carrito en Redis.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import get_mongo_connection, get_redis_connection
from src.transform import transform_all

def load_products_to_mongodb(df: pd.DataFrame, recreate: bool = True) -> bool:
    """Carga productos de Amazon (ya limpios) a MongoDB."""
    if df is None or df.empty:
        print("[LOAD] No hay datos para cargar a MongoDB")
        return False

    try:
        client, db, collection = get_mongo_connection()
        if collection is None:
            return False

        if recreate:
            collection.delete_many({})
            print("[LOAD] Coleccion limpiada")

        products = []
        for _, row in df.iterrows():
            doc = {
                "product_id": row.get("product_id"),
                "product_name": row.get("product_name"),
                "category": row.get("category"),
                "actual_price": float(row.get("actual_price", 0)) if pd.notna(row.get("actual_price")) else 0,
                "discounted_price": float(row.get("discounted_price", 0)) if pd.notna(row.get("discounted_price")) else 0,
                "discount_percentage": float(row.get("discount_percentage", 0)) if pd.notna(row.get("discount_percentage")) else 0,
                "rating": float(row.get("rating", 0)) if pd.notna(row.get("rating")) else 0,
                "rating_count": int(row.get("rating_count", 0)) if pd.notna(row.get("rating_count")) else 0,
                "about_product": row.get("about_product", ""),
                # Campos de reseñas e imágenes eliminados (ver JUSTIFICACION_ETL.md)
                "stock": 100,
                "total_sales": 0,
                "created_at": datetime.utcnow(),
            }
            products.append(doc)

        result = collection.insert_many(products, ordered=False)
        print(f"[LOAD] {len(result.inserted_ids)} productos cargados a MongoDB")
        client.close()
        return True

    except Exception as e:
        print(f"[LOAD] Error cargando a MongoDB: {e}")
        return False


def load_carts_to_redis(df: pd.DataFrame, simulate_realtime: bool = False) -> bool:
    """Carga eventos de carrito a Redis."""
    if df is None or df.empty:
        print("[LOAD] No hay datos para cargar a Redis")
        return False

    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return False

        redis_client.flushdb()
        print("[LOAD] Redis limpiado")

        carts = {}
        for _, row in df.iterrows():
            cart_id = row["cart_id"]
            if cart_id not in carts:
                carts[cart_id] = {
                    "customer_id": row["customer_id"],
                    "events": [],
                    "total_revenue": 0,
                    "lost_revenue": 0,
                }

            event = {
                "event_time": str(row["event_time"]),
                "event_type": row["event_type"],
                "product_id": row["product_id"],
                "quantity": int(row["quantity"]),
                "stock_before": int(row["stock_before"]),
                "stock_after": int(row["stock_after"]),
                "revenue": float(row["revenue"]),
                "lost_revenue": float(row["lost_revenue"]),
            }
            carts[cart_id]["events"].append(event)
            carts[cart_id]["total_revenue"] += float(row["revenue"])
            carts[cart_id]["lost_revenue"] += float(row["lost_revenue"])

        for cart_id, cart_data in carts.items():
            redis_client.hset(
                f"cart:{cart_id}",
                mapping={
                    "customer_id": cart_data["customer_id"],
                    "events": json.dumps(cart_data["events"]),
                    "total_revenue": cart_data["total_revenue"],
                    "lost_revenue": cart_data["lost_revenue"],
                    "loaded_at": datetime.utcnow().isoformat(),
                },
            )

        print(f"[LOAD] {len(carts)} carritos cargados a Redis")

        if simulate_realtime:
            print("[LOAD] Simulando carritos en tiempo real...")
            _simulate_realtime_carts(redis_client, df)

        redis_client.close()
        return True

    except Exception as e:
        print(f"[LOAD] Error cargando a Redis: {e}")
        return False


def _simulate_realtime_carts(redis_client, df: pd.DataFrame):
    """Simula eventos de carrito en tiempo real."""
    try:
        event_times = pd.to_datetime(df["event_time"]).unique()
        event_times = sorted(event_times)

        start_time = pd.to_datetime(event_times[0])

        for event_time in event_times:
            delay = (event_time - start_time).total_seconds() / 60
            delay = max(0.1, min(delay, 2))

            events_at_time = df[df["event_time"] == str(event_time)]

            for _, row in events_at_time.iterrows():
                cart_id = row["cart_id"]
                event_key = f"cart:realtime:{cart_id}:{row['event_type']}"

                event_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "product_id": row["product_id"],
                    "quantity": int(row["quantity"]),
                    "revenue": float(row["revenue"]),
                }

                redis_client.lpush(event_key, json.dumps(event_data))
                print(f"  [REALTIME] {cart_id}: {row['event_type']} - {row['product_id']}")

            time.sleep(delay)

        print("[LOAD] Simulacion en tiempo real completada")

    except Exception as e:
        print(f"[LOAD] Error en simulacion: {e}")


def load_all(amazon_df: pd.DataFrame = None, cart_df: pd.DataFrame = None, simulate_realtime: bool = False) -> bool:
    """Ejecuta la etapa LOAD completa (carga datos transformados a MongoDB y Redis)."""
    print("\n[LOAD] Iniciando carga de datos...\n")

    # Si no se pasan dataframes, transformar internamente
    if amazon_df is None or cart_df is None:
        result = transform_all()
        if result is None:
            print("[LOAD] No se pudo obtener el dataset procesado.")
            return False

        if isinstance(result, tuple):
            amazon_df, cart_df = result
        else:
            amazon_df = result
            if cart_df is None:
                cart_events_path = Path("data/raw/redis_cart_sim.csv")
                if cart_events_path.is_file():
                    cart_df = pd.read_csv(cart_events_path)
                else:
                    print(f"[LOAD] No se encontro dataset de carritos en {cart_events_path}")
                    return False

    mongo_ok = load_products_to_mongodb(amazon_df)
    redis_ok = load_carts_to_redis(cart_df, simulate_realtime=simulate_realtime)

    return mongo_ok and redis_ok


if __name__ == "__main__":
    load_all(simulate_realtime=False)
