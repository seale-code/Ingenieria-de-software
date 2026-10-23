"""Pruebas que preparé para mis consultas del Sprint 1.

Trabajo con una base de prueba en memoria para no cambiar los datos de mis
compañeros. En las pruebas del stock simulo la respuesta de la base real.
"""

import sqlite3
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.backend.catalogo_busqueda import buscar_productos, consultar_stock


class TestCatalogoBusqueda(unittest.TestCase):
    def setUp(self):
        """Preparo productos de ejemplo antes de ejecutar cada prueba."""
        self.conexion = sqlite3.connect(":memory:")
        self.conexion.row_factory = sqlite3.Row
        self.conexion.executescript("""
            CREATE TABLE categorias (id INTEGER PRIMARY KEY, codigo TEXT, nombre TEXT);
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY,
                codigo TEXT,
                nombre TEXT,
                categoria_id INTEGER
            );
            INSERT INTO categorias VALUES (1, 'CAT-1', 'Analgésicos');
            INSERT INTO productos VALUES (1, 'MED-1', 'Paracetamol', 1);
            INSERT INTO productos VALUES (2, 'MED-2', 'Ibuprofeno', 1);
            INSERT INTO productos VALUES (3, 'MED-3', 'Producto sin stock', 1);
        """)

        @contextmanager
        def conexion_de_prueba(_ruta, *, read_only=False):
            yield self.conexion

        # Solo reemplazo la conexión durante mis pruebas unitarias.
        self.parche = patch(
            "src.backend.catalogo_busqueda.connect_database", conexion_de_prueba
        )
        self.parche.start()

    def tearDown(self):
        """Cierro mis datos de prueba y restauro la conexión original."""
        self.parche.stop()
        self.conexion.close()

    def test_catalogo_completo(self):
        # Compruebo que el catálogo muestre los tres productos de ejemplo.
        self.assertEqual(len(buscar_productos()), 3)

    def test_busqueda_parcial_sin_distinguir_mayusculas(self):
        # La palabra PARA debe encontrar Paracetamol.
        self.assertEqual(buscar_productos("PARA")[0]["producto_codigo"], "MED-1")

    def test_busqueda_sin_resultados(self):
        # Cuando no encuentro coincidencias espero una lista vacía.
        self.assertEqual(buscar_productos("medicamento-inexistente"), [])

    def test_entrada_sql_se_trata_como_texto(self):
        # Una cadena con símbolos SQL no debe cambiar la consulta.
        self.assertEqual(buscar_productos("' OR 1=1 --"), [])

    def test_stock_de_una_sucursal_y_un_producto(self):
        # Simulo productos de la misma sucursal y selecciono uno por código.
        inventario = [
            {"producto_codigo": "MED-1", "sucursal_codigo": "SUR-1", "cantidad": 5},
            {"producto_codigo": "MED-2", "sucursal_codigo": "SUR-1", "cantidad": 0},
        ]
        with patch("src.backend.catalogo_busqueda.get_stock", return_value=inventario) as consulta:
            self.assertEqual(consultar_stock("SUR-1", "MED-1"), [inventario[0]])
            consulta.assert_called_once()
            self.assertEqual(consulta.call_args.kwargs["branch"], "SUR-1")

    def test_stock_sin_registro(self):
        # Si no hay filas de stock, no invento una cantidad.
        with patch("src.backend.catalogo_busqueda.get_stock", return_value=[]):
            self.assertEqual(consultar_stock("SUR-1", "MED-9"), [])

    def test_sucursal_es_obligatoria(self):
        # No debo consultar stock sin saber de qué sucursal se trata.
        with self.assertRaises(ValueError):
            consultar_stock(" ")


if __name__ == "__main__":
    unittest.main()
