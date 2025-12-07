"""
Etapa EXTRACT: Lee datasets crudos de Amazon y simulación de carritos Redis.
Para ETL con MongoDB (catálogo) y Redis (carritos en tiempo real).
"""

from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from src.config import AMAZON_CSV, REDIS_CART_CSV


def _load_csv(path_str: str) -> Optional[pd.DataFrame]:
    """Lee un CSV y devuelve un DataFrame con validaciones básicas."""
    path = Path(path_str)
    if not path.is_file():
        print(f"[EXTRACT] No se encontró el archivo: {path}")
        return None

    df = pd.read_csv(path)
    print(f"[EXTRACT] Leído {len(df)} filas de {path}")

    # Validación 1: Existencia y estructura del archivo
    print(f"[EXTRACT] Estructura: {len(df.columns)} columnas, {len(df)} registros")
    print(f"[EXTRACT] Columnas: {list(df.columns)}")

    # Validación 2: Archivo no vacío
    if len(df) == 0:
        print("[ERROR] El archivo está vacío")
        return None
    print(f"[EXTRACT] [OK] Archivo no vacío")

    # Validación 3: Valores nulos detectados
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        print(f"[EXTRACT] Valores nulos detectados: {null_count} total")
        for col in df.columns:
            nulls = df[col].isnull().sum()
            if nulls > 0:
                print(f"  - {col}: {nulls} nulos ({nulls/len(df)*100:.1f}%)")
    else:
        print(f"[EXTRACT] [OK] Sin valores nulos")

    # Validación 4: Duplicados detectados
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        print(f"[EXTRACT] Duplicados detectados: {duplicate_count} registros")
    else:
        print(f"[EXTRACT] [OK] Sin duplicados")

    # Validación 5: Detección de valores atípicos en columnas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        print(f"[EXTRACT] Columnas numéricas detectadas: {list(numeric_cols)}")
        for col in numeric_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            print(f"  - {col}: min={min_val}, max={max_val}")

    # Validación 6: Detección de formatos de fecha/hora
    date_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if date_cols:
        print(f"[EXTRACT] Columnas de fecha/hora detectadas: {date_cols}")
        for col in date_cols:
            try:
                valid_dates = pd.to_datetime(df[col], errors='coerce')
                invalid_count = valid_dates.isnull().sum() - df[col].isnull().sum()
                if invalid_count > 0:
                    print(f"  - {col}: {invalid_count} fechas con formato incorrecto")
                else:
                    print(f"  - {col}: [OK] Todas las fechas válidas")
            except Exception as e:
                print(f"  - {col}: Error en validación - {e}")

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
