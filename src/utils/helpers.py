"""
Módulo UTILS: Funciones auxiliares compartidas del pipeline ETL.

Este módulo contiene funciones helper reutilizables para:
- Conversión segura de tipos de datos
- Limpieza de formatos (precios, porcentajes)
- Persistencia de archivos
- Validaciones comunes

Autor: ETL Team
Fecha: 2025
"""

from pathlib import Path
from typing import Union

import pandas as pd


# ========================================================================
# CONVERSIÓN SEGURA DE TIPOS
# ========================================================================


def safe_float_conversion(value, default: float = 0.0) -> float:
    """
    Convierte un valor a float de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Valor convertido a float o default
    """
    if pd.notna(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    return default


def safe_int_conversion(value, default: int = 0) -> int:
    """
    Convierte un valor a int de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Valor convertido a int o default
    """
    if pd.notna(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return default


def safe_numeric_conversion(series: pd.Series, default: float = 0) -> pd.Series:
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
# LIMPIEZA DE FORMATOS
# ========================================================================


def clean_price_column(series: pd.Series) -> pd.Series:
    """
    Limpia una columna de precios removiendo símbolos y comas.

    Args:
        series: Serie de pandas con valores de precio

    Returns:
        Serie con precios limpios
    """
    return (
        series.astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )


def clean_percentage_column(series: pd.Series) -> pd.Series:
    """
    Limpia una columna de porcentajes removiendo el símbolo %.

    Args:
        series: Serie de pandas con valores de porcentaje

    Returns:
        Serie con porcentajes limpios
    """
    return series.astype(str).str.replace("%", "", regex=False).str.strip()


# ========================================================================
# PERSISTENCIA DE DATOS
# ========================================================================


def save_dataframe_to_csv(
    df: pd.DataFrame,
    output_dir: Union[str, Path],
    filename: str
) -> bool:
    """
    Guarda un DataFrame en CSV.

    Args:
        df: DataFrame a guardar
        output_dir: Directorio de salida
        filename: Nombre del archivo (sin ruta)

    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        out_path = Path(output_dir) / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"[UTILS] Dataset guardado en {out_path}")
        return True
    except Exception as e:
        print(f"[UTILS] Error guardando CSV: {e}")
        return False


# ========================================================================
# VALIDACIONES
# ========================================================================


def validate_dataframe(df: pd.DataFrame, name: str = "DataFrame") -> bool:
    """
    Valida que un DataFrame no sea None ni esté vacío.

    Args:
        df: DataFrame a validar
        name: Nombre descriptivo para mensajes

    Returns:
        True si el DataFrame es válido, False en caso contrario
    """
    if df is None:
        print(f"[UTILS] {name} es None")
        return False

    if df.empty:
        print(f"[UTILS] {name} está vacío")
        return False

    return True


def clip_to_range(
    series: pd.Series,
    min_value: float,
    max_value: float
) -> pd.Series:
    """
    Limita los valores de una serie a un rango específico.

    Args:
        series: Serie de pandas
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido

    Returns:
        Serie con valores dentro del rango
    """
    return series.clip(lower=min_value, upper=max_value)
