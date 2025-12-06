"""
Fase TRANSFORM: limpia y transforma datos de productos y carritos.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from src.config import PROCESSED_CSV


def transform_amazon_products(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Transforma y limpia datos de productos Amazon."""
    if df is None or df.empty:
        return None

    df = df.copy()

    # Eliminar marca (no se desea guardar brand)
    if "brand" in df.columns:
        df = df.drop(columns=["brand"])
        

    # ---------------------------------------------------------
    # NUEVO: FILTRO PARA ELIMINAR SIN NOMBRE Y SIN ID
    # ---------------------------------------------------------
    # 1. Eliminar filas donde product_name sea explícitamente NaN/None
    df = df.dropna(subset=["product_name"])
    df = df.dropna(subset=["product_id"])
    
    # 2. Eliminar filas donde el nombre sea un string vacío ("") o solo espacios ("   ")
    # Esto es importante porque a veces el csv trae comillas vacías que no cuentan como NaN
    df = df[df["product_name"].astype(str).str.strip() != ""]
    df = df[df["product_id"].astype(str).str.strip() != ""]

    # ---------------------------------------------------------
    # ELIMINAR CAMPOS INNECESARIOS PARA ETL
    # ---------------------------------------------------------
    # Campos de reseñas e imágenes no son necesarios para análisis de productos/carritos
    campos_innecesarios = ['user_id', 'user_name', 'review_id', 'review_title',
                           'review_content', 'img_link', 'product_link']
    df = df.drop(columns=[col for col in campos_innecesarios if col in df.columns], errors='ignore')
    print("[TRANSFORM] Campos de reseñas e imágenes eliminados (no necesarios para ETL)")

    # Rellenar faltantes
    df["category"] = df["category"].fillna("Uncategorized")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
    df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce").fillna(0)
    df["about_product"] = df["about_product"].fillna("")

    # Limpiar precios (remover simbolos y comas)
    df["actual_price"] = (
        df["actual_price"].astype(str).str.replace("₹", "").str.replace(",", "").str.strip()
    )
    df["discounted_price"] = (
        df["discounted_price"].astype(str).str.replace("₹", "").str.replace(",", "").str.strip()
    )
    df["discount_percentage"] = df["discount_percentage"].astype(str).str.replace("%", "").str.strip()

    # Convertir a numerico
    df["actual_price"] = pd.to_numeric(df["actual_price"], errors="coerce").fillna(0)
    df["discounted_price"] = pd.to_numeric(df["discounted_price"], errors="coerce").fillna(0)
    df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce").fillna(0)

    # Validar rangos
    df["discount_percentage"] = df["discount_percentage"].clip(lower=0, upper=100)
    df["rating"] = df["rating"].clip(lower=0, upper=5)

    print(f"[TRANSFORM] {len(df)} productos Amazon transformados")
    return df


def transform_redis_carts(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Transforma y limpia datos de carritos."""
    if df is None or df.empty:
        return None

    df = df.copy()

    # Convertir timestamps
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")

    # Validar cantidades
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["quantity"] = df["quantity"].clip(lower=1, upper=100)

    # Convertir stocks y revenue
    df["stock_before"] = pd.to_numeric(df["stock_before"], errors="coerce").fillna(0).astype(int)
    df["stock_after"] = pd.to_numeric(df["stock_after"], errors="coerce").fillna(0).astype(int)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0).astype(float)
    df["lost_revenue"] = pd.to_numeric(df["lost_revenue"], errors="coerce").fillna(0).astype(float)

    print(f"[TRANSFORM] {len(df)} eventos de carrito transformados")
    return df


def get_transformation_stats(amazon_df: Optional[pd.DataFrame], cart_df: Optional[pd.DataFrame]) -> dict:
    """Obtiene estadisticas de transformacion."""
    stats = {
        "products": {
            "total": len(amazon_df) if amazon_df is not None else 0,
            "categories": amazon_df["category"].nunique() if amazon_df is not None else 0,
            "avg_discount": amazon_df["discount_percentage"].mean() if amazon_df is not None else 0,
            "avg_rating": amazon_df["rating"].mean() if amazon_df is not None else 0,
        },
        "carts": {
            "total_events": len(cart_df) if cart_df is not None else 0,
            "unique_carts": cart_df["cart_id"].nunique() if cart_df is not None else 0,
            "unique_customers": cart_df["customer_id"].nunique() if cart_df is not None else 0,
            "total_revenue": cart_df["revenue"].sum() if cart_df is not None else 0,
            "lost_revenue": cart_df["lost_revenue"].sum() if cart_df is not None else 0,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    return stats


def transform_all() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Ejecuta la etapa TRANSFORM completa."""
    from src.extract import extract_all

    print("\n[TRANSFORM] Iniciando transformacion...\n")

    amazon_df, redis_cart_df = extract_all()

    amazon_transformed = transform_amazon_products(amazon_df)
    cart_transformed = transform_redis_carts(redis_cart_df)

    stats = get_transformation_stats(amazon_transformed, cart_transformed)

    print("\n[TRANSFORM] Estadisticas:")
    print(f"  Productos: {stats['products']['total']}")
    print(f"  Categorias: {stats['products']['categories']}")
    print(f"  Rating Promedio: {stats['products']['avg_rating']:.2f}")
    print(f"  Carritos: {stats['carts']['unique_carts']}")
    print(f"  Ingresos: ${stats['carts']['total_revenue']:.2f}")
    print(f"  Ingresos Perdidos: ${stats['carts']['lost_revenue']:.2f}")

    # Guardar dataset limpio en data/processed
    if amazon_transformed is not None:
        out_path = Path(PROCESSED_CSV)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        amazon_transformed.to_csv(out_path, index=False)
        print(f"[TRANSFORM] Dataset procesado guardado en {out_path}")

    return amazon_transformed, cart_transformed


if __name__ == "__main__":
    transform_all()
