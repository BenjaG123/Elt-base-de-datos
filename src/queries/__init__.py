"""
Paquete QUERIES: Consultas independientes a datos crudos.

Este paquete permite consultar directamente los datos almacenados
en MongoDB y Redis sin necesidad de ejecutar el pipeline ETL completo.

Casos de uso:
- Consultas ad-hoc para análisis exploratorio
- Debugging y verificación de datos
- Reportes independientes
- Testing de datos crudos
"""

from src.queries.mongo_queries import (
    count_products_by_category,
    get_all_products,
    get_product_by_id,
    get_products_by_category,
    get_products_by_price_range,
    get_top_rated_products,
)
from src.queries.redis_queries import (
    count_carts_by_customer,
    get_all_cart_ids,
    get_cart_by_id,
    get_cart_events,
    get_carts_by_customer,
    get_total_revenue,
)

__all__ = [
    # MongoDB queries - Products
    "get_all_products",
    "get_product_by_id",
    "get_products_by_category",
    "get_products_by_price_range",
    "get_top_rated_products",
    "count_products_by_category",
    # Redis queries - Carts
    "get_all_cart_ids",
    "get_cart_by_id",
    "get_carts_by_customer",
    "get_cart_events",
    "count_carts_by_customer",
    "get_total_revenue",
]
