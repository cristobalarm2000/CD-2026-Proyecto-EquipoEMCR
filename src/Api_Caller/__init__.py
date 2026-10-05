"""Paquete Api_Caller: Centralización de conexión, inventario y catálogos de la API PJUD."""

from .pjud_client import (
    PJUDClient,
    ENDPOINTS_MAP,
    COMPETENCIAS_MAP,
    MAPA_COMPETENCIAS_INVERSO,
    norm_col,
    cargar_catalogo_cortes,
    cargar_catalogo_tribunales,
    consolidar_a_parquet,
    CORTES_CSV_PATH,
    TRIBUNALES_CSV_PATH,
    SWAGGER_JSON_PATH,
    ENDPOINTS_CSV_PATH
)

__all__ = [
    "PJUDClient",
    "ENDPOINTS_MAP",
    "COMPETENCIAS_MAP",
    "MAPA_COMPETENCIAS_INVERSO",
    "norm_col",
    "cargar_catalogo_cortes",
    "cargar_catalogo_tribunales",
    "consolidar_a_parquet",
    "CORTES_CSV_PATH",
    "TRIBUNALES_CSV_PATH",
    "SWAGGER_JSON_PATH",
    "ENDPOINTS_CSV_PATH"
]
