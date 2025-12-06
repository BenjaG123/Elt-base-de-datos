"""
Configuracion centralizada para MongoDB, Redis y rutas del dataset de Flipkart.
"""

from pymongo import MongoClient
import redis

# ===== CONFIGURACION MONGODB =====
# Aca se guardan los datos de productos ya limpios
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "amazon_db"
MONGO_COLLECTION = "amazon_products"


def get_mongo_connection(collection_name: str = MONGO_COLLECTION):
    """Obtiene conexion a MongoDB (coleccion elegible)."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[collection_name]

        client.server_info()  # Probar conexion
        print("Conectado a MongoDB")

        return client, db, collection
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return None, None, None


# ===== CONFIGURACION REDIS =====
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


def get_redis_connection():
    """Obtiene conexion a Redis."""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

        r.ping()  # Probar conexion
        print("Conectado a Redis")

        return r
    except Exception as e:
        print(f"Error conectando a Redis: {e}")
        return None


# ===== RUTAS DE ARCHIVOS =====
AMAZON_CSV = "data/raw/amazon.csv"
REDIS_CART_CSV = "data/raw/redis_cart_sim.csv"
PROCESSED_CSV = "data/processed/amazon_processed.csv"

if __name__ == "__main__":
    print("Probando configuracion...")
    print(f"Dataset Amazon: {AMAZON_CSV}")

    print("\nProbando conexiones...")

    mongo_client, mongo_db, mongo_col = get_mongo_connection()
    redis_client = get_redis_connection()

    if mongo_client and redis_client:
        print("\nTodas las conexiones funcionan!")
    else:
        print("\nRevisa tu configuracion")
