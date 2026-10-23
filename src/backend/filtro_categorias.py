
from src.database.database import get_stock, DEFAULT_DATABASE


def filtrar_productos_por_categoria(
    categoria=None,
    busqueda="",
    db_path=DEFAULT_DATABASE
):
    """
    Filtra productos por categoría y nombre.

    categoria: código de la categoría.
    busqueda: texto para buscar por nombre.
    db_path: ruta de la base de datos SQLite.

    Si no se indica categoría, devuelve
    productos de todas las categorías.
    """

    if categoria == "":
        categoria = None

    registros = get_stock(
        path=db_path,
        category=categoria,
        search=busqueda
    )

    productos = {}

    for registro in registros:
        codigo = registro["producto_codigo"]

        if codigo not in productos:
            productos[codigo] = {
                "codigo": codigo,
                "nombre": registro["producto"],
                "categoria_codigo": registro["categoria_codigo"],
                "categoria": registro["categoria"]
            }

    return list(productos.values())
