"""
Pipeline ETL completo + Simulador Cyber Day
1. Carga productos Amazon a MongoDB
2. Simula Cyber Day (compras en tiempo real)
3. Analiza resultados (productos vendidos, categorías, pérdidas, etc.)
4. Genera visualizaciones
"""

import sys
from datetime import datetime

# Importar módulos del pipeline
from src.extract import extract_all
from src.transform import transform_all, get_transformation_stats
from src.load import load_products_to_mongodb
from src.simulator import run_simulation
from src.analytics import generate_analytics_report
from src.visualizations import generate_all_visualizations


def print_header(title: str):
    """Imprime encabezado formateado."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_footer():
    """Imprime pie formateado."""
    print("=" * 70 + "\n")


def main():
    """Ejecuta el pipeline ETL completo con simulación."""
    
    print_header("🚀 CYBERDAY SIMULATOR: Amazon Products + MongoDB + Redis")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_footer()

    # ===== ETAPA 1: CARGA DE PRODUCTOS A MONGODB =====
    print_header("📥 ETAPA 1: CARGAR PRODUCTOS AMAZON A MONGODB")
    
    # Extraer y transformar productos
    amazon_df, _ = extract_all()
    
    if amazon_df is None:
        print("[ERROR] No se pudo cargar el dataset de Amazon")
        sys.exit(1)
    
    amazon_transformed, _ = transform_all()
    
    # Cargar a MongoDB
    load_success = load_products_to_mongodb(amazon_transformed, recreate=True)
    
    if not load_success:
        print("[ERROR] No se pudieron cargar productos a MongoDB")
        print("  ⚠️  Asegúrate de que MongoDB esté ejecutándose: mongod")
        sys.exit(1)
    
    print(f"✅ {len(amazon_transformed)} productos cargados a MongoDB")
    print_footer()

    # ===== ETAPA 2: SIMULACIÓN DEL CYBER DAY =====
    print_header("🎮 ETAPA 2: SIMULACIÓN DEL CYBER DAY")
    print("Generando eventos de compra en tiempo real...")
    print("(Esto tomará unos segundos)\n")
    
    # Ejecutar simulación
    # Ajusta estos parámetros según necesites:
    # - num_customers: cuántos clientes participan
    # - num_events: cuántos eventos de compra generar
    simulation_df = run_simulation(
        num_customers=100,  # 100 clientes
        num_events=500,     # 500 eventos de compra
        save_csv=True       # Guardar en CSV
    )
    
    if simulation_df is None:
        print("[ERROR] La simulación falló")
        sys.exit(1)
    
    print_footer()

    # ===== ETAPA 3: ANÁLISIS DE RESULTADOS =====
    print_header("📊 ETAPA 3: ANÁLISIS DE RESULTADOS")
    
    report = generate_analytics_report()
    
    if not report:
        print("[ADVERTENCIA] No se pudo generar el reporte completo")
    
    print_footer()

    # ===== ETAPA 4: VISUALIZACIONES =====
    print_header("📈 ETAPA 4: GENERANDO VISUALIZACIONES")
    
    try:
        generate_all_visualizations()
        print("✅ Visualizaciones guardas en data/processed/")
    except Exception as e:
        print(f"[ADVERTENCIA] Error generando visualizaciones: {e}")
    
    print_footer()

    # ===== RESUMEN FINAL =====
    print_header("🎊 CYBER DAY COMPLETADO")
    
    if simulation_df is not None:
        total_revenue = simulation_df['revenue'].sum()
        total_lost = simulation_df['lost_revenue'].sum()
        total_potential = total_revenue + total_lost
        
        print(f"📦 Total productos en catálogo: {len(amazon_transformed)}")
        print(f"🛒 Total eventos simulados: {len(simulation_df)}")
        print(f"👥 Clientes únicos: {simulation_df['customer_id'].nunique()}")
        print(f"🛍️  Carritos únicos: {simulation_df['cart_id'].nunique()}")
        print(f"\n💰 Ingresos obtenidos: ${total_revenue:,.2f}")
        print(f"❌ Ingresos perdidos: ${total_lost:,.2f}")
        print(f"💎 Potencial total: ${total_potential:,.2f}")
        print(f"📊 Tasa de conversión: {(total_revenue / total_potential * 100):.1f}%")
        
    print(f"\n📅 Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_footer()

    print("✨ ¡Análisis completado exitosamente!")
    print("\n📁 Archivos generados:")
    print("   - data/processed/cyberday_simulation.csv")
    print("   - data/processed/*.png (gráficos)")


if __name__ == "__main__":
    main()