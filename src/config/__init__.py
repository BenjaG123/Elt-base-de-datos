"""
Paquete CONFIG: Configuraciones del sistema.

Este paquete contiene configuraciones de bases de datos,
constantes y parámetros del sistema.
"""

from src.config.database import (
    AMAZON_CSV,
    MONGO_COLLECTION,
    MONGO_DB,
    MONGO_URI,
    PROCESSED_CSV,
    REDIS_CART_CSV,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
    get_mongo_connection,
    get_redis_connection,
)

__all__ = [
    "MONGO_URI",
    "MONGO_DB",
    "MONGO_COLLECTION",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "AMAZON_CSV",
    "REDIS_CART_CSV",
    "PROCESSED_CSV",
    "get_mongo_connection",
    "get_redis_connection",
]
