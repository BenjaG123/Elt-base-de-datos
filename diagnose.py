"""
Script de diagnóstico para verificar la configuración del proyecto.
"""

def check_mongodb():
    """Verifica conexión a MongoDB."""
    print("\n🔍 Verificando MongoDB...")
    try:
        from src.config import get_mongo_connection
        client, db, collection = get_mongo_connection()
        if collection is not None:
            count = collection.count_documents({})
            print(f"   ✅ MongoDB conectado ({count} documentos en colección)")
            client.close()
            return True
        else:
            print("   ❌ No se pudo conectar a MongoDB")
            print("      → Inicia MongoDB con: mongod")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("      → Asegúrate de que MongoDB esté instalado e iniciado")
        return False


def check_redis():
    """Verifica conexión a Redis."""
    print("\n🔍 Verificando Redis...")
    try:
        from src.config import get_redis_connection
        redis_client = get_redis_connection()
        if redis_client is not None:
            keys_count = len(redis_client.keys("*"))
            print(f"   ✅ Redis conectado ({keys_count} claves)")
            redis_client.close()
            return True
        else:
            print("   ❌ No se pudo conectar a Redis")
            print("      → Inicia Redis con: redis-server")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("      → Asegúrate de que Redis esté instalado e iniciado")
        return False


def check_dataset():
    """Verifica que el dataset exista."""
    print("\n🔍 Verificando Dataset Amazon...")
    try:
        from pathlib import Path
        amazon_csv = Path("data/raw/amazon.csv")
        if amazon_csv.is_file():
            import pandas as pd
            df = pd.read_csv(amazon_csv)
            print(f"   ✅ Dataset encontrado ({len(df)} productos)")
            return True
        else:
            print(f"   ❌ Dataset no encontrado en: {amazon_csv}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    print("\n🔍 Verificando dependencias de Python...")
    required = ['pymongo', 'redis', 'pandas', 'matplotlib', 'seaborn']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} no instalado")
            missing.append(package)
    
    if missing:
        print(f"\n   → Instala con: pip install {' '.join(missing)}")
        return False
    return True


def main():
    """Ejecuta diagnóstico completo."""
    print("="*70)
    print(" 🏥 DIAGNÓSTICO DEL SISTEMA")
    print("="*70)
    
    results = {
        'Python Dependencies': check_dependencies(),
        'Dataset Amazon': check_dataset(),
        'MongoDB': check_mongodb(),
        'Redis': check_redis()
    }
    
    print("\n" + "="*70)
    print(" 📋 RESUMEN")
    print("="*70)
    
    all_ok = all(results.values())
    
    for component, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {component}")
    
    if all_ok:
        print("\n🎉 ¡Todo listo! Ejecuta: python main.py")
    else:
        print("\n⚠️  Hay problemas que resolver antes de continuar")
        print("   Ver instrucciones arriba")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
