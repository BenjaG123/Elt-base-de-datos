"""
Visualizaciones para análisis del Cyberday: MongoDB + Redis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from src.config import get_mongo_connection, get_redis_connection
from pathlib import Path

# Crear directorio de salida si no existe
Path("data/processed").mkdir(parents=True, exist_ok=True)


def plot_top_selling_products():
    """Gráfico de productos más vendidos."""
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
            events = json.loads(cart_data.get("events", "[]"))
            
            for event in events:
                if event['event_type'] in ['checkout', 'partial_checkout']:
                    product_id = event['product_id']
                    quantity = event['quantity']
                    sales[product_id] = sales.get(product_id, 0) + quantity
        
        # Obtener nombres de productos
        top_products = sorted(sales.items(), key=lambda x: x[1], reverse=True)[:15]
        
        product_names = []
        quantities = []
        
        for product_id, qty in top_products:
            product = collection.find_one({'product_id': product_id})
            name = product['product_name'][:40] if product else product_id
            product_names.append(name)
            quantities.append(qty)
        
        plt.figure(figsize=(12, 8))
        plt.barh(product_names, quantities, color="steelblue")
        plt.xlabel("Unidades Vendidas")
        plt.title("Top 15 Productos Más Vendidos - Cyber Day")
        plt.tight_layout()
        plt.savefig("data/processed/top_selling_products.png", dpi=100, bbox_inches="tight")
        print("[VIZ] ✅ Gráfico guardado: top_selling_products.png")
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
            total_revenue += float(cart_data.get("total_revenue", 0))
            total_lost += float(cart_data.get("lost_revenue", 0))

        if total_revenue == 0 and total_lost == 0:
            print("[VIZ] No hay datos de ingresos")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Gráfico 1: Barras comparativas
        categories = ["Ingresos\nObtenidos", "Ingresos\nPerdidos"]
        values = [total_revenue, total_lost]
        colors = ["#27ae60", "#e74c3c"]
        
        bars = ax1.bar(categories, values, color=colors, alpha=0.7)
        ax1.set_ylabel("Rupias (₹)")
        ax1.set_title("Ingresos Totales vs Perdidos")
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'₹{int(height):,}',
                    ha='center', va='bottom', fontweight='bold')

        # Gráfico 2: Pie chart
        total = total_revenue + total_lost
        percentages = [total_revenue/total*100, total_lost/total*100]
        
        ax2.pie(percentages, labels=categories, colors=colors,
                autopct='%1.1f%%', startangle=90)
        ax2.set_title("Distribución de Ingresos Potenciales")

        plt.tight_layout()
        plt.savefig("data/processed/revenue_comparison.png", dpi=100, bbox_inches="tight")
        print("[VIZ] ✅ Gráfico guardado: revenue_comparison.png")
        plt.close()

        redis_client.close()

    except Exception as e:
        print(f"[VIZ] Error en comparación de ingresos: {e}")


def generate_all_visualizations():
    """Genera todas las visualizaciones."""
    print("\n[VIZ] 📊 Generando visualizaciones del Cyberday...\n")
    
    plot_top_selling_products()
    plot_top_categories()
    plot_lost_revenue_breakdown()
    plot_stock_out_times()
    plot_revenue_comparison()
    
    print("\n[VIZ] ✅ Todas las visualizaciones completadas\n")


if __name__ == "__main__":
    generate_all_visualizations()
