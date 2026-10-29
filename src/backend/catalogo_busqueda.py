"""Mis consultas del catálogo y del stock para el Sprint 1 de Inkafarma.

En este módulo trabajo mis issues #5 y #10. Aprovecho la base de datos
SQLite del equipo, así que no necesito crear otra base para mis consultas.
"""

from src.database.database import DEFAULT_DATABASE, connect_database, get_stock


def buscar_productos(nombre: str = "", *, db_path=DEFAULT_DATABASE) -> list[dict]:
    """Busco productos por nombre o muestro el catálogo si no paso un filtro.

    Hago una búsqueda parcial sin diferenciar mayúsculas y minúsculas.
    También incluyo productos que todavía no tienen inventario registrado.
    """
    if not isinstance(nombre, str):
        raise ValueError("El nombre buscado debe ser texto")

    # Consulto productos y categorías directamente para no repetir el mismo
    # producto por cada sucursal en la que se encuentre disponible.
    consulta = """
        SELECT p.codigo AS producto_codigo,
               p.nombre AS producto,
               c.codigo AS categoria_codigo,
               c.nombre AS categoria
        FROM productos AS p
        JOIN categorias AS c ON c.id = p.categoria_id
        WHERE instr(casefold(p.nombre), casefold(?)) > 0
        ORDER BY p.codigo
    """

    # Paso el nombre como parámetro, sin concatenarlo al texto de SQL.
    with connect_database(db_path, read_only=True) as conexion:
        conexion.create_function("casefold", 1, str.casefold, deterministic=True)
        filas = conexion.execute(consulta, (nombre.strip(),)).fetchall()
        return [dict(fila) for fila in filas]


def consultar_stock(sucursal: str, producto: str | None = None, *, db_path=DEFAULT_DATABASE) -> list[dict]:
    """Consulto el inventario de una sucursal y, opcionalmente, un producto.

    Si la búsqueda no devuelve registros, retorno una lista vacía. No lo
    interpreto automáticamente como una cantidad cero de existencias.
    """
    if not isinstance(sucursal, str) or not sucursal.strip():
        raise ValueError("Debes indicar el código de la sucursal")
    if producto is not None and (not isinstance(producto, str) or not producto.strip()):
        raise ValueError("El código del producto no puede estar vacío")

    # Reutilizo la consulta de stock que ya tiene nuestro proyecto.
    filas = get_stock(db_path, branch=sucursal.strip())
    if producto is None:
        return filas

    # Si me dan un código, muestro únicamente las coincidencias exactas.
    codigo = producto.strip()
    return [fila for fila in filas if fila["producto_codigo"] == codigo]
