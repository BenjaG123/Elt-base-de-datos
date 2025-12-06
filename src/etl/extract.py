"""
Etapa EXTRACT: Lee datasets crudos de Amazon y simulación de carritos Redis.
Para ETL con MongoDB (catálogo) y Redis (carritos en tiempo real).
"""

from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from src.config import AMAZON_CSV, REDIS_CART_CSV


def _load_csv(path_str: str) -> Optional[pd.DataFrame]:
    """Lee un CSV y devuelve un DataFrame."""
    path = Path(path_str)
    if not path.is_file():
        print(f"[EXTRACT] No se encontró el archivo: {path}")
        return None

    df = pd.read_csv(path)
    print(f"[EXTRACT] Leído {len(df)} filas de {path}")
    return df


def load_amazon_data() -> Optional[pd.DataFrame]:
    """Carga el dataset de productos Amazon para MongoDB."""
    return _load_csv(AMAZON_CSV)


def load_redis_cart_simulation() -> Optional[pd.DataFrame]:
    """Carga la simulación de carritos para Redis."""
    return _load_csv(REDIS_CART_CSV)


def extract_all() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Ejecuta la etapa EXTRACT leyendo ambos datasets."""
    print("\n[EXTRACT] Iniciando extracción de datos...\n")

    amazon_df = load_amazon_data()
    redis_cart_df = load_redis_cart_simulation()

    if amazon_df is not None:
        print(f"\n[EXTRACT] Productos Amazon: {len(amazon_df)} registros")
        print(amazon_df[['product_name', 'discounted_price', 'category']].head(5))

    if redis_cart_df is not None:
        print(f"\n[EXTRACT] Eventos de carrito: {len(redis_cart_df)} eventos")
        print(redis_cart_df[['cart_id', 'event_type', 'product_id', 'quantity']].head(5))

    return amazon_df, redis_cart_df


def main():
    """Ejecuta el módulo EXTRACT de manera independiente."""
    extract_all()


if __name__ == "__main__":
    main()
