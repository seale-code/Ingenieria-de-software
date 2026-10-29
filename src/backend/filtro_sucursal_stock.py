"""Filtrado de productos por sucursal y disponibilidad de stock (Issue #2 - Sprint 1)."""

from src.database.database import DEFAULT_DATABASE, get_stock

MENSAJE_SIN_RESULTADOS = "No se encontraron productos para los filtros seleccionados."


def filtrar_productos_sucursal_stock(
    sucursal: str | None = None,
    solo_disponibles: bool = False,
    categoria: str | None = None,
    busqueda: str = "",
    db_path=DEFAULT_DATABASE,
) -> list[dict]:
    """Filtra el inventario de productos por sucursal, stock disponible, categoría y nombre.

    Parámetros:
        sucursal: código de la sucursal (ej. 'DEMO-NORTE'). Si es None o vacío, incluye todas.
        solo_disponibles: si es True, excluye productos con stock cero (cantidad > 0).
        categoria: código de la categoría (ej. 'DEMO-X'). Si es None o vacío, incluye todas.
        busqueda: texto para buscar parcialmente por nombre del producto.
        db_path: ruta de la base de datos SQLite.
    """
    if isinstance(sucursal, str):
        sucursal = sucursal.strip() or None

    if isinstance(categoria, str):
        categoria = categoria.strip() or None

    if busqueda is None:
        busqueda = ""

    filas = get_stock(
        path=db_path,
        search=busqueda,
        category=categoria,
        branch=sucursal,
        available_only=bool(solo_disponibles),
    )

    return [
        {
            "codigo": fila["producto_codigo"],
            "nombre": fila["producto"],
            "categoria_codigo": fila["categoria_codigo"],
            "categoria": fila["categoria"],
            "sucursal_codigo": fila["sucursal_codigo"],
            "sucursal": fila["sucursal"],
            "cantidad": fila["cantidad"],
            "disponible": fila["cantidad"] > 0,
        }
        for fila in filas
    ]


def consultar_disponibilidad_sucursal(
    sucursal: str | None = None,
    solo_disponibles: bool = False,
    categoria: str | None = None,
    busqueda: str = "",
    db_path=DEFAULT_DATABASE,
) -> dict:
    """Realiza el filtrado e informa explícitamente cuando no hay resultados."""
    productos = filtrar_productos_sucursal_stock(
        sucursal=sucursal,
        solo_disponibles=solo_disponibles,
        categoria=categoria,
        busqueda=busqueda,
        db_path=db_path,
    )

    if not productos:
        return {
            "resultados": [],
            "total": 0,
            "sin_resultados": True,
            "mensaje": MENSAJE_SIN_RESULTADOS,
        }

    return {
        "resultados": productos,
        "total": len(productos),
        "sin_resultados": False,
        "mensaje": f"Se encontraron {len(productos)} producto(s).",
    }
