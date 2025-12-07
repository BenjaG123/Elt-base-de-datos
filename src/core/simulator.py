"""
SIMULADOR DE CYBERDAY
Simula compras en tiempo real, calcula dinero perdido, 
productos más vendidos, categorías, etc.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from src.config import get_mongo_connection, get_redis_connection
import json
import time


class CyberdaySimulator:
    """Simulador de Cyber Day con productos Amazon."""
    
    def __init__(self, num_customers: int = 50, num_events: int = 200):
        """
        Inicializa el simulador.
        
        Args:
            num_customers: Número de clientes simulados
            num_events: Número total de eventos a generar
        """
        self.num_customers = num_customers
        self.num_events = num_events
        self.products = []
        self.simulation_start = datetime.now()
        
    def load_products_from_mongo(self) -> bool:
        """Carga productos desde MongoDB."""
        try:
            _, _, collection = get_mongo_connection()
            if collection is None:
                print("[SIMULATOR] No se pudo conectar a MongoDB")
                return False
            
            # Cargar todos los productos
            self.products = list(collection.find({}))
            print(f"[SIMULATOR] Cargados {len(self.products)} productos de MongoDB")
            
            if not self.products:
                print("[SIMULATOR] No hay productos en MongoDB")
                return False
                
            return True
            
        except Exception as e:
            print(f"[SIMULATOR] Error cargando productos: {e}")
            return False
    
    def simulate_cyberday(self, save_to_redis: bool = True) -> pd.DataFrame:
        """
        Simula un Cyber Day completo.
        
        Returns:
            DataFrame con todos los eventos simulados
        """
        print("\n" + "="*70)
        print("🚀 INICIANDO SIMULACIÓN DE CYBER DAY")
        print("="*70 + "\n")
        
        if not self.load_products_from_mongo():
            return None
        
        events = []
        cart_id = 1
        
        # Diccionario para tracking de stock en tiempo real
        stock_tracker = {}
        stock_out_times = {}  # Guarda el tiempo de agotamiento
        
        for product in self.products:
            stock_tracker[product['product_id']] = product['stock']
        
        # Generar eventos
        current_time = self.simulation_start
        
        for i in range(self.num_events):
            # Seleccionar cliente
            customer_id = f"CUST-{random.randint(1, self.num_customers):03d}"
            
            # Seleccionar producto aleatorio
            product = random.choice(self.products)
            product_id = product['product_id']
            product_name = product['product_name']
            price = product['discounted_price']
            category = product['category']
            
            # Cantidad a comprar (1-5 unidades)
            quantity = random.randint(1, 5)
            
            # Incrementar tiempo
            current_time += timedelta(seconds=random.randint(1, 30))
            
            # Verificar stock disponible
            available_stock = stock_tracker.get(product_id, 0)
            
            # Decidir tipo de evento
            if available_stock <= 0:
                # STOCK AGOTADO - registrar venta perdida
                event_type = "stock_out"
                stock_before = 0
                stock_after = 0
                revenue = 0
                lost_revenue = price * quantity
                
                # Registrar tiempo de agotamiento si es primera vez
                if product_id not in stock_out_times:
                    stock_out_times[product_id] = {
                        'time': current_time,
                        'duration_seconds': (current_time - self.simulation_start).total_seconds(),
                        'product_name': product_name,
                        'category': category
                    }
                    print(f"  ⚠️  AGOTADO: {product_name[:40]}... en {stock_out_times[product_id]['duration_seconds']:.0f}s")
                
            elif available_stock < quantity:
                # Stock insuficiente - compra parcial
                quantity_sold = available_stock
                quantity_lost = quantity - available_stock
                
                event_type = "partial_checkout"
                stock_before = available_stock
                stock_after = 0
                revenue = price * quantity_sold
                lost_revenue = price * quantity_lost
                
                stock_tracker[product_id] = 0
                
                # Registrar agotamiento
                if product_id not in stock_out_times:
                    stock_out_times[product_id] = {
                        'time': current_time,
                        'duration_seconds': (current_time - self.simulation_start).total_seconds(),
                        'product_name': product_name,
                        'category': category
                    }
                    print(f"  ⚠️  AGOTADO: {product_name[:40]}... en {stock_out_times[product_id]['duration_seconds']:.0f}s")
                
            else:
                # Stock disponible - decisión aleatoria
                action = random.choices(
                    ['checkout', 'add', 'abandon'],
                    weights=[0.6, 0.3, 0.1],  # 60% checkout, 30% add, 10% abandon
                    k=1
                )[0]
                
                stock_before = available_stock
                
                if action == 'checkout':
                    event_type = "checkout"
                    stock_after = available_stock - quantity
                    revenue = price * quantity
                    lost_revenue = 0
                    stock_tracker[product_id] = stock_after
                    
                elif action == 'add':
                    event_type = "add"
                    stock_after = available_stock  # No se descuenta aún
                    revenue = 0
                    lost_revenue = 0
                    
                else:  # abandon
                    event_type = "abandon"
                    stock_after = available_stock
                    revenue = 0
                    lost_revenue = 0
            
            # Crear evento
            event = {
                'cart_id': f"CART-{cart_id:03d}",
                'customer_id': customer_id,
                'event_time': current_time,
                'event_type': event_type,
                'product_id': product_id,
                'product_name': product_name,
                'category': category,
                'quantity': quantity,
                'price': price,
                'stock_before': stock_before,
                'stock_after': stock_after,
                'revenue': revenue,
                'lost_revenue': lost_revenue
            }
            
            events.append(event)
            
            # Incrementar cart_id aleatoriamente
            if random.random() > 0.7:  # 30% chance de nuevo carrito
                cart_id += 1
        
        # Crear DataFrame
        df = pd.DataFrame(events)
        
        # Guardar tiempos de agotamiento en Redis si se solicita
        if save_to_redis:
            self._save_events_to_redis(df)  #  ← PRIMERO los carritos (con flush)
            self._save_stock_out_times_to_redis(stock_out_times)  # ← DESPUÉS los stock_out
        
        print(f"\n✅ Simulación completada: {len(events)} eventos generados")
        print(f"   Carritos únicos: {df['cart_id'].nunique()}")
        print(f"   Clientes únicos: {df['customer_id'].nunique()}")
        print(f"   Productos agotados: {len(stock_out_times)}")
        
        return df
    
    def _save_stock_out_times_to_redis(self, stock_out_times: Dict):
        """Guarda tiempos de agotamiento en Redis."""
        try:
            redis_client = get_redis_connection()
            if redis_client is None:
                return
            
            for product_id, data in stock_out_times.items():
                key = f"stock_out:{product_id}"
                redis_client.hset(key, mapping={
                    'product_name': data['product_name'],
                    'category': data['category'],
                    'time': data['time'].isoformat(),
                    'duration_seconds': data['duration_seconds']
                })
            
            print(f"[SIMULATOR] {len(stock_out_times)} tiempos de agotamiento guardados en Redis")
            redis_client.close()
            
        except Exception as e:
            print(f"[SIMULATOR] Error guardando tiempos de agotamiento: {e}")
    
    def _save_events_to_redis(self, df: pd.DataFrame):
        """Guarda eventos agrupados por carrito en Redis."""
        try:
            redis_client = get_redis_connection()
            if redis_client is None:
                return
            
            # Limpiar Redis
            redis_client.flushdb()
            
            # Agrupar por carrito
            for cart_id in df['cart_id'].unique():
                cart_events = df[df['cart_id'] == cart_id]
                
                events_list = []
                total_revenue = 0
                total_lost = 0
                
                for _, row in cart_events.iterrows():
                    event = {
                        'event_time': row['event_time'].isoformat(),
                        'event_type': row['event_type'],
                        'product_id': row['product_id'],
                        'product_name': row['product_name'],
                        'category': row['category'],
                        'quantity': int(row['quantity']),
                        'price': float(row['price']),
                        'stock_before': int(row['stock_before']),
                        'stock_after': int(row['stock_after']),
                        'revenue': float(row['revenue']),
                        'lost_revenue': float(row['lost_revenue'])
                    }
                    events_list.append(event)
                    total_revenue += row['revenue']
                    total_lost += row['lost_revenue']
                
                # Guardar en Redis
                redis_client.hset(
                    f"cart:{cart_id}",
                    mapping={
                        'customer_id': cart_events.iloc[0]['customer_id'],
                        'events': json.dumps(events_list),
                        'total_revenue': total_revenue,
                        'lost_revenue': total_lost,
                        'created_at': datetime.now().isoformat()
                    }
                )
            
            print(f"[SIMULATOR] {df['cart_id'].nunique()} carritos guardados en Redis")
            redis_client.close()
            
        except Exception as e:
            print(f"[SIMULATOR] Error guardando eventos: {e}")


def run_simulation(num_customers: int = 50, num_events: int = 200, save_csv: bool = True) -> pd.DataFrame:
    """
    Ejecuta la simulación completa.
    
    Args:
        num_customers: Número de clientes
        num_events: Número de eventos
        save_csv: Si guardar el resultado en CSV
        
    Returns:
        DataFrame con todos los eventos
    """
    simulator = CyberdaySimulator(num_customers, num_events)
    df = simulator.simulate_cyberday(save_to_redis=True)
    
    if df is not None and save_csv:
        output_path = "data/processed/cyberday_simulation.csv"
        df.to_csv(output_path, index=False)
        print(f"\n📁 Simulación guardada en: {output_path}")
    
    return df


if __name__ == "__main__":
    # Ejecutar simulación con valores por defecto
    df = run_simulation(num_customers=100, num_events=500)
    
    if df is not None:
        print("\n" + "="*70)
        print("📊 RESUMEN DE LA SIMULACIÓN")
        print("="*70)
        print(f"\nTotal eventos: {len(df)}")
        print(f"Ingresos totales: ${df['revenue'].sum():,.2f}")
        print(f"Ingresos perdidos: ${df['lost_revenue'].sum():,.2f}")
        print(f"Tasa de éxito: {(df['revenue'].sum() / (df['revenue'].sum() + df['lost_revenue'].sum()) * 100):.1f}%")
