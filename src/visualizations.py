"""
Visualizaciones para análisis del Cyberday: MongoDB + Redis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from src.config import get_mongo_connection, get_redis_connection
from pathlib import Path

# Crear directorio de salida si no existe
Path("data/processed").mkdir(parents=True, exist_ok=True)


def plot_product_categories_distribution():
    """Gráfico de distribución de productos por categoría."""
    try:
        _, _, collection = get_mongo_connection()
        if collection is None:
            return

        # Agregación por categoría (Amazon no tiene campo brand)
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15},
        ]

        results = list(collection.aggregate(pipeline))

        if not results:
            print("[VIZ] No hay datos de productos")
            return

        categories = [r["_id"] for r in results]
        counts = [r["count"] for r in results]

        # Crear directorio si no existe
        Path("docs/images").mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.barh(categories, counts, color="steelblue")
        plt.xlabel("Cantidad de Productos")
        plt.title("Top 15 Categorías por Cantidad de Productos - Amazon")
        plt.tight_layout()
        plt.savefig("docs/images/categories_distribution.png", dpi=100, bbox_inches="tight")
        print("[VIZ] Gráfico guardado: docs/images/categories_distribution.png")
        plt.close()

    except Exception as e:
        print(f"[VIZ] Error en gráfico de categorías: {e}")


def plot_price_distribution():
    """Gráfico de distribución de precios."""
    try:
        _, _, collection = get_mongo_connection()
        if collection is None:
            return

        # Obtener precios
        prices = [doc["discounted_price"] for doc in collection.find({}, {"discounted_price": 1}) if doc.get("discounted_price", 0) > 0]

        if not prices:
            print("[VIZ] No hay datos de precios")
            return

        # Crear directorio si no existe
        Path("docs/images").mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.hist(prices, bins=50, color="coral", edgecolor="black", alpha=0.7)
        plt.xlabel("Precio Descuentado (Rupias)")
        plt.ylabel("Cantidad de Productos")
        plt.title("Distribución de Precios - Amazon")
        plt.tight_layout()
        plt.savefig("docs/images/price_distribution.png", dpi=100, bbox_inches="tight")
        print("[VIZ] Gráfico guardado: docs/images/price_distribution.png")
        plt.close()

    except Exception as e:
        print(f"[VIZ] Error en distribución de precios: {e}")


def plot_cart_events_timeline():
    """Gráfico de eventos de carrito en tiempo."""
    try:
        redis_client = get_redis_connection()
        _, _, collection = get_mongo_connection()
        
        if redis_client is None or collection is None:
            return

        # Obtener ventas por producto
        sales = {}
        cart_keys = redis_client.keys("cart:CART-*")
        
        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            try:
                events = json.loads(cart_data.get("events", "[]"))
                for event in events:
                    event_type = event.get("event_type", "unknown")
                    if event_type in events_by_type:
                        events_by_type[event_type] += 1
            except:
                pass

        if sum(events_by_type.values()) == 0:
            print("[VIZ] No hay eventos de carrito")
            return

        # Crear directorio si no existe
        Path("docs/images").mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(10, 6))
        colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12"]
        plt.bar(events_by_type.keys(), events_by_type.values(), color=colors)
        plt.xlabel("Tipo de Evento")
        plt.ylabel("Cantidad de Eventos")
        plt.title("Eventos de Carrito - Cyberday Amazon")
        plt.tight_layout()
        plt.savefig("docs/images/cart_events.png", dpi=100, bbox_inches="tight")
        print("[VIZ] Gráfico guardado: docs/images/cart_events.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en productos más vendidos: {e}")


def plot_top_categories():
    """Gráfico de categorías más vendidas."""
    try:
        redis_client = get_redis_connection()
        
        if redis_client is None:
            return

        # Obtener ventas por categoría
        category_sales = {}
        cart_keys = redis_client.keys("cart:CART-*")
        
        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))
            
            for event in events:
                if event['event_type'] in ['checkout', 'partial_checkout']:
                    category = event.get('category', 'Unknown')
                    main_category = category.split('|')[0] if '|' in category else category
                    revenue = event.get('revenue', 0)
                    category_sales[main_category] = category_sales.get(main_category, 0) + revenue
        
        if not category_sales:
            print("[VIZ] No hay datos de categorías")
            return
        
        # Top 10 categorías
        top_categories = sorted(category_sales.items(), key=lambda x: x[1], reverse=True)[:10]
        categories = [c[0][:30] for c in top_categories]
        revenues = [c[1] for c in top_categories]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(categories)), revenues, color="coral")
        plt.xticks(range(len(categories)), categories, rotation=45, ha='right')
        plt.ylabel("Revenue Total (₹)")
        plt.title("Top 10 Categorías Más Vendidas - Cyber Day")
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'₹{int(height):,}',
                    ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig("data/processed/top_categories.png", dpi=100, bbox_inches="tight")
        print("[VIZ] ✅ Gráfico guardado: top_categories.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en categorías: {e}")


def plot_lost_revenue_breakdown():
    """Gráfico de ingresos perdidos por categoría."""
    try:
        redis_client = get_redis_connection()
        
        if redis_client is None:
            return

        # Obtener pérdidas por categoría
        lost_by_category = {}
        cart_keys = redis_client.keys("cart:CART-*")
        
        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))
            
            for event in events:
                lost = event.get('lost_revenue', 0)
                if lost > 0:
                    category = event.get('category', 'Unknown')
                    main_category = category.split('|')[0] if '|' in category else category
                    lost_by_category[main_category] = lost_by_category.get(main_category, 0) + lost
        
        if not lost_by_category:
            print("[VIZ] No hay pérdidas registradas")
            return
        
        # Top 10
        top_lost = sorted(lost_by_category.items(), key=lambda x: x[1], reverse=True)[:10]
        categories = [c[0][:25] for c in top_lost]
        losses = [c[1] for c in top_lost]
        
        plt.figure(figsize=(10, 6))
        plt.barh(categories, losses, color="#e74c3c")
        plt.xlabel("Ingresos Perdidos (₹)")
        plt.title("Top 10 Categorías con Mayores Pérdidas - Cyber Day")
        plt.tight_layout()
        plt.savefig("data/processed/lost_revenue_by_category.png", dpi=100, bbox_inches="tight")
        print("[VIZ] ✅ Gráfico guardado: lost_revenue_by_category.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en pérdidas: {e}")


def plot_stock_out_times():
    """Gráfico de tiempos de agotamiento."""
    try:
        redis_client = get_redis_connection()
        
        if redis_client is None:
            return

        stock_out_keys = redis_client.keys("stock_out:*")
        
        if not stock_out_keys:
            print("[VIZ] No hay productos agotados")
            return
        
        times = []
        names = []
        
        for key in stock_out_keys[:15]:  # Top 15 más rápidos
            data = redis_client.hgetall(key)
            duration_min = float(data.get('duration_seconds', 0)) / 60
            name = data.get('product_name', 'Unknown')[:35]
            
            times.append(duration_min)
            names.append(name)
        
        # Ordenar por tiempo ascendente
        sorted_data = sorted(zip(times, names))
        times = [t for t, _ in sorted_data]
        names = [n for _, n in sorted_data]
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(names, times, color="#f39c12")
        plt.xlabel("Tiempo hasta Agotarse (minutos)")
        plt.title("Productos Más Cotizados (se agotaron más rápido)")
        
        # Agregar valores
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{width:.1f} min',
                    ha='left', va='center', fontsize=8)
        
        plt.tight_layout()
        plt.savefig("data/processed/stock_out_times.png", dpi=100, bbox_inches="tight")
        print("[VIZ] ✅ Gráfico guardado: stock_out_times.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en tiempos de agotamiento: {e}")


def plot_revenue_comparison():
    """Gráfico comparativo: ingresos vs pérdidas."""
    try:
        redis_client = get_redis_connection()
        
        if redis_client is None:
            return

        cart_keys = redis_client.keys("cart:CART-*")
        total_revenue = 0
        total_lost = 0

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            revenue = float(cart_data.get("total_revenue", 0))
            lost = float(cart_data.get("lost_revenue", 0))

            total_revenue += revenue
            lost_revenue += lost

            if revenue > 0:
                revenue_by_cart.append(revenue)

        if total_revenue == 0 and total_lost == 0:
            print("[VIZ] No hay datos de ingresos")
            return

        # Crear directorio si no existe
        Path("docs/images").mkdir(parents=True, exist_ok=True)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Gráfico 1: Ingresos vs Perdidos
        ax1.bar(["Ingresos", "Perdidos"], [total_revenue, lost_revenue], color=["#27ae60", "#e74c3c"])
        ax1.set_ylabel("Rupias")
        ax1.set_title("Ingresos Totales vs Perdidos - Amazon")
        for i, v in enumerate([total_revenue, lost_revenue]):
            ax1.text(i, v + 100, f"${v:.0f}", ha="center", va="bottom", fontweight="bold")

        # Gráfico 2: Pie chart
        total = total_revenue + total_lost
        percentages = [total_revenue/total*100, total_lost/total*100]
        
        ax2.pie(percentages, labels=categories, colors=colors,
                autopct='%1.1f%%', startangle=90)
        ax2.set_title("Distribución de Ingresos Potenciales")

        plt.tight_layout()
        plt.savefig("docs/images/revenue_metrics.png", dpi=100, bbox_inches="tight")
        print("[VIZ] Gráfico guardado: docs/images/revenue_metrics.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en comparación de ingresos: {e}")


def generate_all_visualizations():
    """Genera todas las visualizaciones."""
    print("\n[VIZ] Generando visualizaciones del Cyberday Amazon...\n")

    plot_product_categories_distribution()
    plot_price_distribution()
    plot_cart_events_timeline()
    plot_revenue_metrics()

    print("\n[VIZ] Todas las visualizaciones completadas\n")


"""
Visualizaciones para analisis del Cyberday: MongoDB + Redis.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

from src.config import get_mongo_connection, get_redis_connection


# Directorio de salida para las imagenes
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_product_categories_distribution():
    """Grafico de distribucion de productos por categoria."""
    try:
        mongo_client, _, collection = get_mongo_connection()
        if collection is None:
            return

        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15},
        ]

        results = list(collection.aggregate(pipeline))
        if not results:
            print("[VIZ] No hay datos de productos")
            return

        categories = [r.get("_id", "Sin categoria") for r in results]
        counts = [r["count"] for r in results]

        plt.figure(figsize=(12, 6))
        plt.barh(categories, counts, color="steelblue")
        plt.xlabel("Cantidad de productos")
        plt.title("Top 15 categorias por cantidad de productos - Amazon")
        plt.tight_layout()
        output_path = OUTPUT_DIR / "categories_distribution.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        mongo_client.close()

    except Exception as e:
        print(f"[VIZ] Error en grafico de categorias: {e}")


def plot_price_distribution():
    """Grafico de distribucion de precios."""
    try:
        mongo_client, _, collection = get_mongo_connection()
        if collection is None:
            return

        prices = [
            doc.get("discounted_price", 0)
            for doc in collection.find({}, {"discounted_price": 1})
            if doc.get("discounted_price", 0) > 0
        ]

        if not prices:
            print("[VIZ] No hay datos de precios")
            return

        plt.figure(figsize=(12, 6))
        plt.hist(prices, bins=50, color="coral", edgecolor="black", alpha=0.7)
        plt.xlabel("Precio descontado")
        plt.ylabel("Cantidad de productos")
        plt.title("Distribucion de precios - Amazon")
        plt.tight_layout()
        output_path = OUTPUT_DIR / "price_distribution.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        mongo_client.close()

    except Exception as e:
        print(f"[VIZ] Error en distribucion de precios: {e}")


def plot_cart_events_timeline():
    """Grafico de eventos de carrito por tipo."""
    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return

        events_by_type = {
            "add": 0,
            "checkout": 0,
            "partial_checkout": 0,
            "abandon": 0,
            "stock_out": 0,
        }

        cart_keys = redis_client.keys("cart:CART-*")
        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))
            for event in events:
                event_type = event.get("event_type", "unknown")
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

        total_events = sum(events_by_type.values())
        if total_events == 0:
            print("[VIZ] No hay eventos de carrito")
            return

        plt.figure(figsize=(10, 6))
        colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6"]
        plt.bar(events_by_type.keys(), events_by_type.values(), color=colors[: len(events_by_type)])
        plt.xlabel("Tipo de evento")
        plt.ylabel("Cantidad de eventos")
        plt.title("Eventos de carrito - Cyberday Amazon")
        plt.tight_layout()
        output_path = OUTPUT_DIR / "cart_events.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en eventos de carrito: {e}")


def plot_top_selling_products():
    """Grafico de productos mas vendidos."""
    try:
        redis_client = get_redis_connection()
        mongo_client, _, collection = get_mongo_connection()

        if redis_client is None or collection is None:
            return

        sales = {}
        cart_keys = redis_client.keys("cart:CART-*")

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))

            for event in events:
                if event.get("event_type") in ["checkout", "partial_checkout"]:
                    product_id = event.get("product_id")
                    quantity = event.get("quantity", 0)
                    if product_id:
                        sales[product_id] = sales.get(product_id, 0) + quantity

        if not sales:
            print("[VIZ] No hay ventas registradas")
            return

        top_products = sorted(sales.items(), key=lambda x: x[1], reverse=True)[:15]

        product_names = []
        quantities = []

        for product_id, qty in top_products:
            product = collection.find_one({"product_id": product_id})
            name = product.get("product_name", product_id) if product else product_id
            product_names.append(str(name)[:40])
            quantities.append(qty)

        plt.figure(figsize=(12, 8))
        plt.barh(product_names, quantities, color="steelblue")
        plt.xlabel("Unidades vendidas")
        plt.title("Top 15 productos mas vendidos - Cyber Day")
        plt.tight_layout()
        output_path = OUTPUT_DIR / "top_selling_products.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()
        mongo_client.close()

    except Exception as e:
        print(f"[VIZ] Error en productos mas vendidos: {e}")


def plot_top_categories():
    """Grafico de categorias mas vendidas."""
    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return

        category_sales = {}
        cart_keys = redis_client.keys("cart:CART-*")

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))

            for event in events:
                if event.get("event_type") in ["checkout", "partial_checkout"]:
                    category = event.get("category", "Unknown")
                    main_category = category.split("|")[0] if "|" in category else category
                    revenue = event.get("revenue", 0)
                    category_sales[main_category] = category_sales.get(main_category, 0) + revenue

        if not category_sales:
            print("[VIZ] No hay datos de categorias")
            return

        top_categories = sorted(category_sales.items(), key=lambda x: x[1], reverse=True)[:10]
        categories = [c[0][:30] for c in top_categories]
        revenues = [c[1] for c in top_categories]

        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(categories)), revenues, color="coral")
        plt.xticks(range(len(categories)), categories, rotation=45, ha="right")
        plt.ylabel("Revenue total")
        plt.title("Top 10 categorias mas vendidas - Cyber Day")

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height):,}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        plt.tight_layout()
        output_path = OUTPUT_DIR / "top_categories.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en categorias: {e}")


def plot_lost_revenue_breakdown():
    """Grafico de ingresos perdidos por categoria."""
    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return

        lost_by_category = {}
        cart_keys = redis_client.keys("cart:CART-*")

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            events = json.loads(cart_data.get("events", "[]"))

            for event in events:
                lost = event.get("lost_revenue", 0)
                if lost > 0:
                    category = event.get("category", "Unknown")
                    main_category = category.split("|")[0] if "|" in category else category
                    lost_by_category[main_category] = lost_by_category.get(main_category, 0) + lost

        if not lost_by_category:
            print("[VIZ] No hay perdidas registradas")
            return

        top_lost = sorted(lost_by_category.items(), key=lambda x: x[1], reverse=True)[:10]
        categories = [c[0][:25] for c in top_lost]
        losses = [c[1] for c in top_lost]

        plt.figure(figsize=(10, 6))
        plt.barh(categories, losses, color="#e74c3c")
        plt.xlabel("Ingresos perdidos")
        plt.title("Top 10 categorias con mayores perdidas - Cyber Day")
        plt.tight_layout()
        output_path = OUTPUT_DIR / "lost_revenue_by_category.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en perdidas: {e}")


def plot_stock_out_times():
    """Grafico de tiempos de agotamiento."""
    try:
        redis_client = get_redis_connection()
        if redis_client is None:
            return

        stock_out_keys = redis_client.keys("stock_out:*")

        if not stock_out_keys:
            print("[VIZ] No hay productos agotados")
            return

        times = []
        names = []

        for key in list(stock_out_keys)[:15]:
            data = redis_client.hgetall(key)
            duration_min = float(data.get("duration_seconds", 0)) / 60
            name = data.get("product_name", "Unknown")[:35]

            times.append(duration_min)
            names.append(name)

        sorted_data = sorted(zip(times, names))
        times = [t for t, _ in sorted_data]
        names = [n for _, n in sorted_data]

        plt.figure(figsize=(12, 8))
        bars = plt.barh(names, times, color="#f39c12")
        plt.xlabel("Tiempo hasta agotarse (minutos)")
        plt.title("Productos mas cotizados (se agotaron mas rapido)")

        for bar in bars:
            width = bar.get_width()
            plt.text(
                width,
                bar.get_y() + bar.get_height() / 2.0,
                f"{width:.1f} min",
                ha="left",
                va="center",
                fontsize=8,
            )

        plt.tight_layout()
        output_path = OUTPUT_DIR / "stock_out_times.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en tiempos de agotamiento: {e}")


def plot_revenue_comparison():
    """Grafico comparativo: ingresos vs perdidas."""
    try:
        redis_client = get_redis_connection()

        if redis_client is None:
            return

        cart_keys = redis_client.keys("cart:CART-*")
        total_revenue = 0
        total_lost = 0

        for key in cart_keys:
            cart_data = redis_client.hgetall(key)
            total_revenue += float(cart_data.get("total_revenue", 0))
            total_lost += float(cart_data.get("lost_revenue", 0))

        if total_revenue == 0 and total_lost == 0:
            print("[VIZ] No hay datos de ingresos")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        categories = ["Ingresos\nObtenidos", "Ingresos\nPerdidos"]
        values = [total_revenue, total_lost]
        colors = ["#27ae60", "#e74c3c"]

        bars = ax1.bar(categories, values, color=colors, alpha=0.7)
        ax1.set_ylabel("Rupias")
        ax1.set_title("Ingresos totales vs perdidos")

        for bar in bars:
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height):,}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        total = total_revenue + total_lost
        percentages = [total_revenue / total * 100, total_lost / total * 100]

        ax2.pie(percentages, labels=categories, colors=colors, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Distribucion de ingresos potenciales")

        plt.tight_layout()
        output_path = OUTPUT_DIR / "revenue_comparison.png"
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print(f"[VIZ] Grafico guardado: {output_path}")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en comparacion de ingresos: {e}")


def generate_all_visualizations():
    """Genera todas las visualizaciones."""
    print("\n[VIZ] Generando visualizaciones del Cyberday...\n")

    plot_product_categories_distribution()
    plot_price_distribution()
    plot_cart_events_timeline()
    plot_top_selling_products()
    plot_top_categories()
    plot_lost_revenue_breakdown()
    plot_stock_out_times()
    plot_revenue_comparison()

    print("\n[VIZ] Todas las visualizaciones completadas\n")


if __name__ == "__main__":
    generate_all_visualizations()
