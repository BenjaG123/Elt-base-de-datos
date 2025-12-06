"""
ANALYTICS: Análisis completo del Cyber Day
- Productos más vendidos
- Categorías más vendidas  
- Dinero perdido por producto/categoría
- Tiempo de agotamiento
- Análisis cruzado MongoDB + Redis
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
from src.config import get_mongo_connection, get_redis_connection


class CyberdayAnalytics:
    """Análisis completo del Cyber Day."""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.redis_client = None
        
    def connect(self) -> bool:
        """Conecta a MongoDB y Redis."""
        try:
            self.mongo_client, self.mongo_db, self.mongo_collection = get_mongo_connection()
            self.redis_client = get_redis_connection()
            
            if self.mongo_collection is None or self.redis_client is None:
                print("[ANALYTICS] Error: No se pudo conectar a las bases de datos")
                return False
                
            return True
        except Exception as e:
            print(f"[ANALYTICS] Error en conexión: {e}")
            return False
    
    def close(self):
        """Cierra conexiones."""
        if self.mongo_client:
            self.mongo_client.close()
        if self.redis_client:
            self.redis_client.close()
    
    def get_top_selling_products(self, limit: int = 10) -> pd.DataFrame:
        """
        Productos más vendidos.
        Cruza datos de Redis (ventas) con MongoDB (info producto).
        """
        print("\n📊 ANÁLISIS: Productos más vendidos")
        print("-" * 70)
        
        try:
            # Obtener ventas de Redis
            sales_by_product = {}
            revenue_by_product = {}
            
            cart_keys = self.redis_client.keys("cart:CART-*")
            
            for key in cart_keys:
                cart_data = self.redis_client.hgetall(key)
                events = json.loads(cart_data.get('events', '[]'))
                
                for event in events:
                    if event['event_type'] in ['checkout', 'partial_checkout']:
                        product_id = event['product_id']
                        quantity = event['quantity']
                        revenue = event['revenue']
                        
                        sales_by_product[product_id] = sales_by_product.get(product_id, 0) + quantity
                        revenue_by_product[product_id] = revenue_by_product.get(product_id, 0) + revenue
            
            # Enriquecer con datos de MongoDB
            results = []
            for product_id, quantity_sold in sorted(sales_by_product.items(), key=lambda x: x[1], reverse=True)[:limit]:
                product = self.mongo_collection.find_one({'product_id': product_id})
                
                if product:
                    results.append({
                        'product_id': product_id,
                        'product_name': product['product_name'],
                        'category': product['category'],
                        'price': product['discounted_price'],
                        'quantity_sold': quantity_sold,
                        'revenue': revenue_by_product[product_id],
                        'original_stock': product['stock']
                    })
            
            df = pd.DataFrame(results)
            
            if not df.empty:
                print(df[['product_name', 'quantity_sold', 'revenue']].head(10).to_string(index=False))
            
            return df
            
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
            return pd.DataFrame()
    
    def get_top_categories(self) -> pd.DataFrame:
        """Categorías más vendidas con revenue total."""
        print("\n📊 ANÁLISIS: Categorías más vendidas")
        print("-" * 70)
        
        try:
            # Obtener ventas de Redis por producto
            sales_by_product = {}
            revenue_by_product = {}
            
            cart_keys = self.redis_client.keys("cart:CART-*")
            
            for key in cart_keys:
                cart_data = self.redis_client.hgetall(key)
                events = json.loads(cart_data.get('events', '[]'))
                
                for event in events:
                    if event['event_type'] in ['checkout', 'partial_checkout']:
                        product_id = event['product_id']
                        category = event.get('category', 'Unknown')
                        quantity = event['quantity']
                        revenue = event['revenue']
                        
                        # Agrupar por categoría principal (primera parte antes del |)
                        main_category = category.split('|')[0] if '|' in category else category
                        
                        if main_category not in sales_by_product:
                            sales_by_product[main_category] = 0
                            revenue_by_product[main_category] = 0
                        
                        sales_by_product[main_category] += quantity
                        revenue_by_product[main_category] += revenue
            
            # Crear DataFrame
            results = []
            for category in sales_by_product:
                results.append({
                    'category': category,
                    'total_units_sold': sales_by_product[category],
                    'total_revenue': revenue_by_product[category],
                    'avg_price_per_unit': revenue_by_product[category] / sales_by_product[category] if sales_by_product[category] > 0 else 0
                })
            
            df = pd.DataFrame(results).sort_values('total_revenue', ascending=False)
            
            if not df.empty:
                print(df.head(10).to_string(index=False))
            
            return df
            
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
            return pd.DataFrame()
    
    def get_lost_revenue_analysis(self) -> Dict:
        """Análisis completo de ingresos perdidos."""
        print("\n💰 ANÁLISIS: Dinero perdido por falta de stock")
        print("-" * 70)
        
        try:
            lost_by_product = {}
            lost_by_category = {}
            total_lost = 0
            total_revenue = 0
            
            cart_keys = self.redis_client.keys("cart:CART-*")
            
            for key in cart_keys:
                cart_data = self.redis_client.hgetall(key)
                events = json.loads(cart_data.get('events', '[]'))
                
                for event in events:
                    product_id = event['product_id']
                    category = event.get('category', 'Unknown')
                    main_category = category.split('|')[0] if '|' in category else category
                    lost_revenue = event.get('lost_revenue', 0)
                    revenue = event.get('revenue', 0)
                    
                    total_lost += lost_revenue
                    total_revenue += revenue
                    
                    if lost_revenue > 0:
                        if product_id not in lost_by_product:
                            lost_by_product[product_id] = {
                                'product_name': event.get('product_name', 'Unknown'),
                                'category': main_category,
                                'lost_revenue': 0,
                                'lost_units': 0
                            }
                        
                        lost_by_product[product_id]['lost_revenue'] += lost_revenue
                        lost_by_product[product_id]['lost_units'] += event.get('quantity', 0)
                        
                        # Por categoría
                        lost_by_category[main_category] = lost_by_category.get(main_category, 0) + lost_revenue
            
            # Top productos con más pérdidas
            top_lost_products = sorted(
                lost_by_product.items(),
                key=lambda x: x[1]['lost_revenue'],
                reverse=True
            )[:10]
            
            # Top categorías con más pérdidas
            top_lost_categories = sorted(
                lost_by_category.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            print(f"\n💵 TOTAL PERDIDO: ${total_lost:,.2f}")
            print(f"💵 TOTAL VENDIDO: ${total_revenue:,.2f}")
            print(f"📊 % PERDIDO: {(total_lost / (total_lost + total_revenue) * 100):.1f}%")
            
            print("\n🔝 TOP 10 PRODUCTOS CON MÁS PÉRDIDAS:")
            for i, (product_id, data) in enumerate(top_lost_products, 1):
                print(f"{i:2d}. {data['product_name'][:50]:50s} ${data['lost_revenue']:>10,.2f} ({data['lost_units']} unidades)")
            
            print("\n📦 TOP 10 CATEGORÍAS CON MÁS PÉRDIDAS:")
            for i, (category, lost) in enumerate(top_lost_categories, 1):
                print(f"{i:2d}. {category[:40]:40s} ${lost:>10,.2f}")
            
            return {
                'total_lost': total_lost,
                'total_revenue': total_revenue,
                'lost_percentage': (total_lost / (total_lost + total_revenue) * 100) if (total_lost + total_revenue) > 0 else 0,
                'lost_by_product': dict(top_lost_products),
                'lost_by_category': dict(top_lost_categories)
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
            return {}
    
    def get_stock_out_times(self) -> pd.DataFrame:
        """Productos más cotizados (se agotaron más rápido)."""
        print("\n⏱️  ANÁLISIS: Tiempo de agotamiento (productos más cotizados)")
        print("-" * 70)
        
        try:
            stock_out_keys = self.redis_client.keys("stock_out:*")
            
            if not stock_out_keys:
                print("No hay productos agotados registrados.")
                return pd.DataFrame()
            
            results = []
            for key in stock_out_keys:
                data = self.redis_client.hgetall(key)
                product_id = key.replace('stock_out:', '')
                
                results.append({
                    'product_id': product_id,
                    'product_name': data.get('product_name', 'Unknown'),
                    'category': data.get('category', 'Unknown'),
                    'duration_seconds': float(data.get('duration_seconds', 0)),
                    'duration_minutes': float(data.get('duration_seconds', 0)) / 60,
                    'stock_out_time': data.get('time', '')
                })
            
            df = pd.DataFrame(results).sort_values('duration_seconds')
            
            print("\n🔥 PRODUCTOS MÁS COTIZADOS (se agotaron más rápido):")
            print(df[['product_name', 'duration_minutes', 'category']].head(10).to_string(index=False))
            
            # Análisis por categoría
            category_avg = df.groupby('category')['duration_minutes'].agg(['mean', 'count']).sort_values('mean')
            print("\n📦 CATEGORÍAS QUE SE AGOTAN MÁS RÁPIDO (promedio):")
            print(category_avg.head(10).to_string())
            
            return df
            
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
            return pd.DataFrame()
    
    def get_customer_behavior(self) -> Dict:
        """Análisis de comportamiento de clientes."""
        print("\n👥 ANÁLISIS: Comportamiento de clientes")
        print("-" * 70)
        
        try:
            customer_stats = {}
            
            cart_keys = self.redis_client.keys("cart:CART-*")
            
            for key in cart_keys:
                cart_data = self.redis_client.hgetall(key)
                customer_id = cart_data.get('customer_id', 'Unknown')
                events = json.loads(cart_data.get('events', '[]'))
                
                if customer_id not in customer_stats:
                    customer_stats[customer_id] = {
                        'total_carts': 0,
                        'total_revenue': 0,
                        'total_lost': 0,
                        'checkouts': 0,
                        'abandons': 0
                    }
                
                customer_stats[customer_id]['total_carts'] += 1
                customer_stats[customer_id]['total_revenue'] += float(cart_data.get('total_revenue', 0))
                customer_stats[customer_id]['total_lost'] += float(cart_data.get('lost_revenue', 0))
                
                for event in events:
                    if event['event_type'] == 'checkout':
                        customer_stats[customer_id]['checkouts'] += 1
                    elif event['event_type'] == 'abandon':
                        customer_stats[customer_id]['abandons'] += 1
            
            total_customers = len(customer_stats)
            avg_revenue = sum(s['total_revenue'] for s in customer_stats.values()) / total_customers if total_customers > 0 else 0
            
            print(f"Total clientes: {total_customers}")
            print(f"Revenue promedio por cliente: ${avg_revenue:,.2f}")
            
            # Top clientes
            top_customers = sorted(
                customer_stats.items(),
                key=lambda x: x[1]['total_revenue'],
                reverse=True
            )[:5]
            
            print("\n🏆 TOP 5 CLIENTES:")
            for i, (customer_id, stats) in enumerate(top_customers, 1):
                print(f"{i}. {customer_id}: ${stats['total_revenue']:,.2f} ({stats['checkouts']} compras)")
            
            return {
                'total_customers': total_customers,
                'avg_revenue_per_customer': avg_revenue,
                'customer_stats': customer_stats
            }
            
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
            return {}
    
    def get_complete_report(self) -> Dict:
        """Genera reporte completo del Cyber Day."""
        print("\n" + "="*70)
        print("📊 REPORTE COMPLETO DEL CYBER DAY")
        print("="*70)
        
        if not self.connect():
            return {}
        
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'top_products': self.get_top_selling_products(),
                'top_categories': self.get_top_categories(),
                'lost_revenue': self.get_lost_revenue_analysis(),
                'stock_out_times': self.get_stock_out_times(),
                'customer_behavior': self.get_customer_behavior()
            }
            
            print("\n" + "="*70)
            print("✅ REPORTE COMPLETADO")
            print("="*70 + "\n")
            
            return report
            
        finally:
            self.close()


def generate_analytics_report():
    """Función principal para generar el reporte."""
    analytics = CyberdayAnalytics()
    return analytics.get_complete_report()


if __name__ == "__main__":
    generate_analytics_report()
