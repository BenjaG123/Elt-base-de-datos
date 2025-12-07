"""
Pipeline ETL completo: Amazon → MongoDB | Redis Cart Simulation
Simula un Cyberday con múltiples productos y carritos en tiempo real.
Flujo del pipeline:
1. VERIFICAR CONEXIONES → MongoDB + Redis
2. EXTRACT → Leer amazon.csv + redis_cart_sim.csv
3. TRANSFORM → Limpiar y transformar datos
4. LOAD → Cargar a MongoDB + Redis
5. SIMULATOR → Simular Cyber Day con eventos en tiempo real
6. INTEGRATION → Análisis cruzado y métricas
7. VISUALIZACIONES → Generar gráficos
8. RESUMEN → Estadísticas finales
"""

import sys
from datetime import datetime

# Importar módulos del pipeline
from src.config import get_mongo_connection, get_redis_connection
from src.core import integration_all, run_simulation
from src.etl import extract_all, get_transformation_stats, load_all, transform_all
from src.visualization import generate_all_visualizations

def print_header(title: str):
    """Imprime encabezado formateado."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_footer():
    """Imprime pie formateado."""
    print("=" * 70 + "\n")


def main():
    """Ejecuta el pipeline ETL completo."""

    print_header("PIPELINE ETL: CYBERDAY AMAZON CON MONGODB Y REDIS")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_footer()

    # ===== VERIFICAR CONEXIONES =====
    print_header("VERIFICANDO CONEXIONES A BASES DE DATOS")

    print("[CONEXION] Verificando MongoDB...")
    mongo_client, mongo_db, mongo_col = get_mongo_connection()
    if mongo_client is None:
        print("[ERROR] No se pudo conectar a MongoDB")
        print("  Asegurate de ejecutar: mongod")
        sys.exit(1)
    mongo_client.close()
    print("[OK] MongoDB conectado exitosamente")

    print("\n[CONEXION] Verificando Redis...")
    redis_client = get_redis_connection()
    if redis_client is None:
        print("[ERROR] No se pudo conectar a Redis")
        print("  Asegurate de ejecutar: redis-server")
        sys.exit(1)
    redis_client.close()
    print("[OK] Redis conectado exitosamente")

    print_footer()

    # ===== ETAPA 1: EXTRACT =====
    print_header("ETAPA 1: EXTRACT (Extraccion)")
    amazon_df, redis_cart_df = extract_all()

    if amazon_df is None or redis_cart_df is None:
        print("[ERROR] No se pudieron cargar los datos")
        sys.exit(1)

    print_footer()

    # ===== ETAPA 2: TRANSFORM =====
    print_header("ETAPA 2: TRANSFORM (Transformacion)")
    amazon_transformed, cart_transformed = transform_all()
    stats = get_transformation_stats(amazon_transformed, cart_transformed)
    print_footer()

    # ===== ETAPA 3: LOAD =====
    print_header("ETAPA 3: LOAD (Carga a MongoDB y Redis)")
    load_success = load_all(amazon_transformed, cart_transformed)

    if not load_success:
        print("[ADVERTENCIA] La carga no fue completamente exitosa")
        print("  Asegurate de que MongoDB y Redis esten ejecutandose")

    print_footer()

    # ===== ETAPA 4: SIMULATOR =====
    print_header("ETAPA 4: SIMULATOR (Simulacion Cyber Day)")
    try:
        simulation_df = run_simulation(num_customers=100, num_events=500, save_csv=True)
        if simulation_df is not None:
            print(f"\n📊 Resumen de Simulacion:")
            print(f"   Total eventos: {len(simulation_df)}")
            print(f"   Ingresos totales: ${simulation_df['revenue'].sum():,.2f}")
            print(f"   Ingresos perdidos: ${simulation_df['lost_revenue'].sum():,.2f}")
            total_possible = simulation_df['revenue'].sum() + simulation_df['lost_revenue'].sum()
            if total_possible > 0:
                print(f"   Tasa de exito: {(simulation_df['revenue'].sum() / total_possible * 100):.1f}%")
        else:
            print("[ADVERTENCIA] La simulacion no genero datos")
    except Exception as e:
        print(f"[ADVERTENCIA] Error en simulacion: {e}")
    print_footer()

    # ===== ETAPA 5: INTEGRATION =====
    print_header("ETAPA 5: INTEGRATION (Analisis Cruzado)")
    report = integration_all()
    print_footer()

    # ===== ETAPA 6: VISUALIZACIONES =====
    print_header("ETAPA 6: VISUALIZACIONES (Graficos)")
    try:
        generate_all_visualizations()
    except Exception as e:
        print(f"[ADVERTENCIA] Error generando visualizaciones: {e}")
    print_footer()

    # ===== RESUMEN FINAL =====
    print_header("RESUMEN DEL PIPELINE")
    print(f"Productos Amazon: {stats['products']['total']}")
    print(f"Categorias: {stats['products']['categories']}")
    print(f"Descuento Promedio: {stats['products']['avg_discount']:.2f}%")
    print(f"Eventos de Carrito: {stats['carts']['total_events']}")
    print(f"Carritos Unicos: {stats['carts']['unique_carts']}")
    print(f"Clientes: {stats['carts']['unique_customers']}")
    print(f"Ingresos Totales: ${stats['carts']['total_revenue']:.2f}")
    print(f"Ingresos Perdidos: ${stats['carts']['lost_revenue']:.2f}")
    print(f"Timestamp: {stats['timestamp']}")
    print_footer()

    print("Pipeline completado exitosamente")


if __name__ == "__main__":
    main()