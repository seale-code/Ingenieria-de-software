
import unittest
import tempfile
from pathlib import Path

from src.database.database import initialize_database
from src.backend.filtro_categorias import (
    filtrar_productos_por_categoria
)


class TestFiltroCategorias(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.db_path = Path(self.temp.name) / "prueba.sqlite3"

        initialize_database(self.db_path, demo=True)

    def filtrar(self, categoria=None, busqueda=""):
        return filtrar_productos_por_categoria(
            categoria=categoria,
            busqueda=busqueda,
            db_path=self.db_path
        )

    def test_filtrar_categoria_demo_x(self):
        productos = self.filtrar("DEMO-X")

        self.assertEqual(
            {p["codigo"] for p in productos},
            {"DEMO-A", "DEMO-C"}
        )

    def test_filtrar_categoria_demo_y(self):
        productos = self.filtrar("DEMO-Y")

        self.assertEqual(
            [p["codigo"] for p in productos],
            ["DEMO-B"]
        )

    def test_mostrar_todos(self):
        productos = self.filtrar()

        self.assertEqual(len(productos), 3)

    def test_limpiar_filtro(self):
        productos = self.filtrar("")

        self.assertEqual(len(productos), 3)

    def test_categoria_inexistente(self):
        productos = self.filtrar("NO-EXISTE")

        self.assertEqual(productos, [])

    def test_buscar_por_nombre(self):
        productos = self.filtrar(
            busqueda="Producto demo A"
        )

        self.assertEqual(
            [p["codigo"] for p in productos],
            ["DEMO-A"]
        )

    def test_categoria_y_busqueda(self):
        productos = self.filtrar(
            categoria="DEMO-X",
            busqueda="Producto demo A"
        )

        self.assertEqual(
            [p["codigo"] for p in productos],
            ["DEMO-A"]
        )

    def test_busqueda_sin_resultados(self):
        productos = self.filtrar(
            categoria="DEMO-X",
            busqueda="Producto demo B"
        )

        self.assertEqual(productos, [])

    def test_sin_productos_duplicados(self):
        productos = self.filtrar()

        codigos = [p["codigo"] for p in productos]

        self.assertEqual(
            len(codigos),
            len(set(codigos))
        )


if __name__ == "__main__":
    unittest.main()
