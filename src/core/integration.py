"""
INTEGRATION: Cruces de datos entre MongoDB (catálogo) y Redis (carritos en tiempo real).
Análisis y métricas para simular un Cyberday.
"""

import json
from datetime import datetime
import pandas as pd
from src.config import get_mongo_connection, get_redis_connection


def get_product_performance_mongodb() -> dict:
    """Obtiene métricas de productos desde MongoDB."""
    try:
        _, _, collection = get_mongo_connection()
        if collection is None:
            return {}

        # Agregación: productos por marca y categoría
        pipeline = [
            {
                "$group": {
                    "_id": "$brand",
                    "count": {"$sum": 1},
                    "avg_price": {"$avg": "$discounted_price"},
                    "avg_rating": {"$avg": "$rating"},
                    "avg_discount": {"$avg": "$discount_percentage"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]

        results = list(collection.aggregate(pipeline))

        metrics = {
            "top_brands": results,
            "total_products": collection.count_documents({}),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return metrics

    except Exception as e:
        print(f"[INTEGRATION] Error en MongoDB: {e}")
        return {}


def get_cart_analytics_redis() -> dict:
    """Obtiene métricas de carritos desde Redis."""
    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return {}

        # Obtener todas las claves de carrito
        cart_keys = redis_client.keys("cart:CART-*")
        
        metrics = {
            "total_carts": 0,
            "total_revenue": 0,
            "lost_revenue": 0,
            "checkout_events": 0,
            "abandoned_carts": 0,
            "carts": [],
        }

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            if not cart_data:
                continue

            metrics["total_carts"] += 1
            metrics["total_revenue"] += float(cart_data.get("total_revenue", 0))
            metrics["lost_revenue"] += float(cart_data.get("lost_revenue", 0))

            # Contar eventos
            try:
                events = json.loads(cart_data.get("events", "[]"))
                for event in events:
                    if event["event_type"] == "checkout":
                        metrics["checkout_events"] += 1
                    elif event["event_type"] == "abandon":
                        metrics["abandoned_carts"] += 1
            except:
                pass

            metrics["carts"].append({
                "cart_id": key.replace("cart:", ""),
                "customer_id": cart_data.get("customer_id", "Unknown"),
                "total_revenue": float(cart_data.get("total_revenue", 0)),
            })

        metrics["timestamp"] = datetime.utcnow().isoformat()
        return metrics

    except Exception as e:
        print(f"[INTEGRATION] Error en Redis: {e}")
        return {}


def enrich_carts_with_product_info():
    """Enriquece los datos de carritos con información de productos."""
    try:
        _, _, mongo_col = get_mongo_connection()
        redis_client = get_redis_connection()

        if mongo_col is None or redis_client is None:
            return False

        # Obtener todos los productos como diccionario
        products = {}
        for doc in mongo_col.find({}, {"product_id": 1, "product_name": 1, "discounted_price": 1}):
            products[doc["product_id"]] = {
                "name": doc.get("product_name", "Unknown"),
                "price": doc.get("discounted_price", 0),
            }

        # Enriquecer carritos
        cart_keys = redis_client.keys("cart:CART-*")
        enriched_count = 0

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            try:
                events = json.loads(cart_data.get("events", "[]"))
                
                for event in events:
                    product_id = event.get("product_id")
                    if product_id in products:
                        event["product_name"] = products[product_id]["name"]
                        event["product_price"] = products[product_id]["price"]

                # Guardar eventos enriquecidos
                redis_client.hset(key, "events_enriched", json.dumps(events))
                enriched_count += 1

            except Exception as e:
                print(f"  Error enriqueciendo {key}: {e}")

        print(f"[INTEGRATION] {enriched_count} carritos enriquecidos")
        redis_client.close()
        return True

    except Exception as e:
        print(f"[INTEGRATION] Error en enriquecimiento: {e}")
        return False


def generate_cyberday_report() -> pd.DataFrame:
    """Genera reporte completo del Cyberday."""
    print("\n[INTEGRATION] Generando reporte del Cyberday...\n")

    # Obtener métricas
    product_metrics = get_product_performance_mongodb()
    cart_metrics = get_cart_analytics_redis()

    # Crear reporte
    report = {
        "Métrica": [],
        "Valor": [],
    }

    # Productos
    report["Métrica"].append("Total de Productos")
    report["Valor"].append(product_metrics.get("total_products", 0))

    # Carritos
    report["Métrica"].append("Total de Carritos")
    report["Valor"].append(cart_metrics.get("total_carts", 0))

    report["Métrica"].append("Carritos Completados")
    report["Valor"].append(cart_metrics.get("checkout_events", 0))

    report["Métrica"].append("Carritos Abandonados")
    report["Valor"].append(cart_metrics.get("abandoned_carts", 0))

    # Ingresos
    report["Métrica"].append("Ingresos Totales")
    report["Valor"].append(f"${cart_metrics.get('total_revenue', 0):.2f}")

    report["Métrica"].append("Ingresos Perdidos")
    report["Valor"].append(f"${cart_metrics.get('lost_revenue', 0):.2f}")

    # Tasas
    total_carts = cart_metrics.get("total_carts", 1)
    checkout_rate = (cart_metrics.get("checkout_events", 0) / total_carts * 100) if total_carts > 0 else 0
    abandon_rate = (cart_metrics.get("abandoned_carts", 0) / total_carts * 100) if total_carts > 0 else 0

    report["Métrica"].append("Tasa de Conversión (%)")
    report["Valor"].append(f"{checkout_rate:.2f}%")

    report["Métrica"].append("Tasa de Abandono (%)")
    report["Valor"].append(f"{abandon_rate:.2f}%")

    df_report = pd.DataFrame(report)

    print(df_report.to_string(index=False))
    print()

    return df_report


def integration_all():
    """Ejecuta la etapa INTEGRATION completa."""
    print("\n[INTEGRATION] Iniciando análisis cruzado...\n")

    enrich_carts_with_product_info()
    report = generate_cyberday_report()

    return report


if __name__ == "__main__":
    integration_all()