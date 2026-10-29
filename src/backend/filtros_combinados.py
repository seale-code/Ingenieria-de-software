"""Validación y consulta de filtros combinados con búsqueda por nombre (S1-03 / Issue #8)."""

from src.backend.filtro_sucursal_stock import (
    MENSAJE_SIN_RESULTADOS,
    filtrar_productos_sucursal_stock,
)
from src.database.database import DEFAULT_DATABASE


def validar_y_filtrar_catalogo(
    busqueda: str = "",
    categoria: str | None = None,
    sucursal: str | None = None,
    solo_disponibles: bool = False,
    db_path=DEFAULT_DATABASE,
) -> dict:
    """Ejecuta la búsqueda por nombre combinada con categoría, sucursal y disponibilidad.

    Valida los parámetros de entrada, aplica los filtros de manera conjunta y
    devuelve un diccionario con los resultados y el mensaje informativo cuando
    no existen coincidencias (cumpliendo S1-03 y el caso de prueba S1-CP-07).
    """
    if busqueda is None:
        busqueda = ""
    if not isinstance(busqueda, str):
        raise ValueError("El texto de búsqueda debe ser una cadena de texto.")

    if categoria is not None and not isinstance(categoria, str):
        raise ValueError("El código de categoría debe ser una cadena de texto o None.")

    if sucursal is not None and not isinstance(sucursal, str):
        raise ValueError("El código de sucursal debe ser una cadena de texto o None.")

    if not isinstance(solo_disponibles, bool):
        raise ValueError("El parámetro solo_disponibles debe ser booleano (True/False).")

    categoria_limpia = categoria.strip() if isinstance(categoria, str) and categoria.strip() else None
    sucursal_limpia = sucursal.strip() if isinstance(sucursal, str) and sucursal.strip() else None
    busqueda_limpia = busqueda.strip()

    resultados = filtrar_productos_sucursal_stock(
        sucursal=sucursal_limpia,
        solo_disponibles=solo_disponibles,
        categoria=categoria_limpia,
        busqueda=busqueda_limpia,
        db_path=db_path,
    )

    filtros_activos = {
        "busqueda": busqueda_limpia,
        "categoria": categoria_limpia,
        "sucursal": sucursal_limpia,
        "solo_disponibles": solo_disponibles,
    }

    if not resultados:
        return {
            "resultados": [],
            "total": 0,
            "sin_resultados": True,
            "mensaje": MENSAJE_SIN_RESULTADOS,
            "filtros_aplicados": filtros_activos,
        }

    return {
        "resultados": resultados,
        "total": len(resultados),
        "sin_resultados": False,
        "mensaje": f"Se encontraron {len(resultados)} resultado(s).",
        "filtros_aplicados": filtros_activos,
    }
