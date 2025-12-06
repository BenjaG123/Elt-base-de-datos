"""
Módulo TRANSFORM: Limpieza y transformación de datos del pipeline ETL.

Este módulo implementa la fase T (Transform) del proceso ETL, realizando:
- Validación de integridad de datos
- Normalización de formatos (precios, porcentajes, fechas)
- Limpieza de valores faltantes y outliers
- Aplicación de reglas de negocio
- Generación de estadísticas de calidad de datos

Fuentes de datos:
- Amazon Products: Catálogo de productos con precios y ratings
- Redis Cart Events: Eventos de carritos de compra en tiempo real

Autor: ETL Team
Fecha: 2025
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import pandas as pd

from src.extract import extract_all

# ========================================================================
# CONSTANTES DE VALIDACIÓN DE NEGOCIO
# ========================================================================
# Rangos válidos para métricas de productos y carritos

# Ratings de productos (sistema de 5 estrellas)
MIN_RATING = 0.0
MAX_RATING = 5.0

# Descuentos promocionales (porcentaje)
MIN_DISCOUNT = 0.0
MAX_DISCOUNT = 100.0

# Cantidades por transacción (límites de negocio)
MIN_QUANTITY = 1
MAX_QUANTITY = 100

# Valores por defecto
DEFAULT_CATEGORY = "Uncategorized"


# ========================================================================
# FUNCIONES HELPER PRIVADAS
# ========================================================================


def _clean_price_column(series: pd.Series) -> pd.Series:
    """
    Limpia una columna de precios removiendo símbolos y comas.

    Args:
        series: Serie de pandas con valores de precio

    Returns:
        Serie con precios limpios convertidos a float
    """
    return (
        series.astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )


def _clean_percentage_column(series: pd.Series) -> pd.Series:
    """
    Limpia una columna de porcentajes removiendo el símbolo %.

    Args:
        series: Serie de pandas con valores de porcentaje

    Returns:
        Serie con porcentajes limpios
    """
    return series.astype(str).str.replace("%", "", regex=False).str.strip()


def _safe_numeric_conversion(series: pd.Series, default: float = 0) -> pd.Series:
    """
    Convierte una serie a numérico de forma segura.

    Args:
        series: Serie de pandas a convertir
        default: Valor por defecto para valores inválidos

    Returns:
        Serie convertida a numérico
    """
    return pd.to_numeric(series, errors="coerce").fillna(default)


# ========================================================================
# FUNCIONES DE TRANSFORMACIÓN PRINCIPALES
# ========================================================================


def transform_amazon_products(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Transforma y limpia datos de productos Amazon.

    Operaciones realizadas:
    - Elimina columnas innecesarias (brand, reviews, imágenes)
    - Filtra productos sin nombre o ID
    - Normaliza precios y porcentajes de descuento
    - Valida rangos de rating y descuentos
    - Rellena valores faltantes

    Args:
        df: DataFrame con datos crudos de productos Amazon

    Returns:
        DataFrame transformado o None si el input es inválido
    """
    if df is None or df.empty:
        return None

    df = df.copy()

    # Eliminar columna 'brand' - no requerida para análisis de productos
    if "brand" in df.columns:
        df = df.drop(columns=["brand"])

    # Validación de integridad: eliminar registros sin identificadores críticos
    # Paso 1: Remover filas con valores NaN/None en campos obligatorios
    df = df.dropna(subset=["product_name", "product_id"])

    # Paso 2: Filtrar strings vacíos o solo espacios en blanco
    # Nota: CSV puede contener comillas vacías "" que no son detectadas como NaN
    df = df[df["product_name"].astype(str).str.strip() != ""]
    df = df[df["product_id"].astype(str).str.strip() != ""]

    # Limpieza de esquema: eliminar columnas no utilizadas en el pipeline ETL
    # Estas columnas agregan ruido sin valor para análisis de ventas/carritos
    campos_innecesarios = [
        'user_id', 'user_name', 'review_id', 'review_title',
        'review_content', 'img_link', 'product_link'
    ]
    df = df.drop(
        columns=[col for col in campos_innecesarios if col in df.columns],
        errors='ignore'
    )
    print("[TRANSFORM] Campos de metadata eliminados (reviews, links, usuarios)")

    # Normalización de valores faltantes con valores por defecto semánticamente correctos
    df["category"] = df["category"].fillna(DEFAULT_CATEGORY)
    df["rating"] = _safe_numeric_conversion(df["rating"], default=0)
    df["rating_count"] = _safe_numeric_conversion(df["rating_count"], default=0)
    df["about_product"] = df["about_product"].fillna("")

    # Limpieza y conversión de columnas monetarias
    # Remueve símbolos de moneda (₹), separadores de miles (,) y convierte a float
    df["actual_price"] = _safe_numeric_conversion(
        _clean_price_column(df["actual_price"]), default=0
    )
    df["discounted_price"] = _safe_numeric_conversion(
        _clean_price_column(df["discounted_price"]), default=0
    )
    df["discount_percentage"] = _safe_numeric_conversion(
        _clean_percentage_column(df["discount_percentage"]), default=0
    )

    # Validación de rangos: aplicar límites de negocio a valores numéricos
    # Descuentos: 0-100%, Ratings: 0-5 estrellas
    df["discount_percentage"] = df["discount_percentage"].clip(
        lower=MIN_DISCOUNT, upper=MAX_DISCOUNT
    )
    df["rating"] = df["rating"].clip(lower=MIN_RATING, upper=MAX_RATING)

    print(f"[TRANSFORM] {len(df)} productos Amazon transformados")
    return df


def transform_redis_carts(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Transforma y limpia datos de eventos de carrito.

    Operaciones realizadas:
    - Convierte timestamps a formato datetime
    - Valida cantidades dentro de rangos permitidos
    - Normaliza valores de stock y revenue
    - Convierte tipos de datos apropiados

    Args:
        df: DataFrame con eventos crudos de carrito

    Returns:
        DataFrame transformado o None si el input es inválido
    """
    if df is None or df.empty:
        return None

    df = df.copy()

    # Conversión temporal: parsear timestamps a objetos datetime de pandas
    # Permite operaciones temporales y análisis de series de tiempo
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")

    # Validación de cantidades: asegurar valores dentro de límites de negocio
    # Rango permitido: 1-100 unidades por transacción
    df["quantity"] = _safe_numeric_conversion(df["quantity"], default=MIN_QUANTITY).astype(int)
    df["quantity"] = df["quantity"].clip(lower=MIN_QUANTITY, upper=MAX_QUANTITY)

    # Conversión de métricas de inventario y financieras
    # Stock: valores enteros no negativos
    # Revenue: valores flotantes para precisión monetaria
    df["stock_before"] = _safe_numeric_conversion(df["stock_before"], default=0).astype(int)
    df["stock_after"] = _safe_numeric_conversion(df["stock_after"], default=0).astype(int)
    df["revenue"] = _safe_numeric_conversion(df["revenue"], default=0).astype(float)
    df["lost_revenue"] = _safe_numeric_conversion(df["lost_revenue"], default=0).astype(float)

    print(f"[TRANSFORM] {len(df)} eventos de carrito transformados")
    return df


# ========================================================================
# FUNCIONES DE MÉTRICAS Y ESTADÍSTICAS
# ========================================================================


def get_transformation_stats(
    amazon_df: Optional[pd.DataFrame], cart_df: Optional[pd.DataFrame]
) -> Dict[str, dict]:
    """
    Obtiene estadísticas de transformación.

    Args:
        amazon_df: DataFrame de productos Amazon transformados
        cart_df: DataFrame de eventos de carrito transformados

    Returns:
        Diccionario con estadísticas de productos y carritos
    """
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return stats


# ========================================================================
# FUNCIÓN PRINCIPAL DE ORQUESTACIÓN
# ========================================================================


def transform_all() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Ejecuta la etapa TRANSFORM completa.

    Returns:
        Tupla con (productos Amazon transformados, eventos de carrito transformados)
    """
    print("\n[TRANSFORM] Iniciando transformacion...\n")

    # Paso 1: Extraer datos crudos de fuentes CSV
    amazon_df, redis_cart_df = extract_all()

    # Paso 2: Aplicar transformaciones específicas por tipo de dato
    amazon_transformed = transform_amazon_products(amazon_df)
    cart_transformed = transform_redis_carts(redis_cart_df)

    # Paso 3: Calcular métricas de calidad de datos post-transformación
    stats = get_transformation_stats(amazon_transformed, cart_transformed)

    # Paso 4: Mostrar resumen ejecutivo de la transformación
    print("\n[TRANSFORM] Estadisticas:")
    print(f"  Productos: {stats['products']['total']}")
    print(f"  Categorias: {stats['products']['categories']}")
    print(f"  Rating Promedio: {stats['products']['avg_rating']:.2f}")
    print(f"  Carritos: {stats['carts']['unique_carts']}")
    print(f"  Ingresos: ${stats['carts']['total_revenue']:.2f}")
    print(f"  Ingresos Perdidos: ${stats['carts']['lost_revenue']:.2f}")

    return amazon_transformed, cart_transformed


if __name__ == "__main__":
    transform_all()
