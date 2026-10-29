"""Pruebas unitarias para el filtrado por sucursal y stock disponible (Issue #2)."""

import tempfile
import unittest
from pathlib import Path

from src.backend.filtro_sucursal_stock import (
    MENSAJE_SIN_RESULTADOS,
    consultar_disponibilidad_sucursal,
    filtrar_productos_sucursal_stock,
)
from src.database.database import initialize_database


class TestFiltroSucursalStock(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "prueba_sucursal.sqlite3"
        initialize_database(self.db_path, demo=True)

    def filtrar(
        self,
        sucursal=None,
        solo_disponibles=False,
        categoria=None,
        busqueda="",
    ):
        return filtrar_productos_sucursal_stock(
            sucursal=sucursal,
            solo_disponibles=solo_disponibles,
            categoria=categoria,
            busqueda=busqueda,
            db_path=self.db_path,
        )

    def consultar(
        self,
        sucursal=None,
        solo_disponibles=False,
        categoria=None,
        busqueda="",
    ):
        return consultar_disponibilidad_sucursal(
            sucursal=sucursal,
            solo_disponibles=solo_disponibles,
            categoria=categoria,
            busqueda=busqueda,
            db_path=self.db_path,
        )

    def test_filtrar_por_sucursal_norte(self):
        resultados = self.filtrar(sucursal="DEMO-NORTE")
        self.assertEqual(len(resultados), 3)
        self.assertTrue(
            all(r["sucursal_codigo"] == "DEMO-NORTE" for r in resultados)
        )

    def test_filtrar_por_sucursal_sur(self):
        resultados = self.filtrar(sucursal="DEMO-SUR")
        self.assertEqual(len(resultados), 3)
        self.assertTrue(
            all(r["sucursal_codigo"] == "DEMO-SUR" for r in resultados)
        )

    def test_solo_disponibles_excluye_stock_cero(self):
        resultados = self.filtrar(solo_disponibles=True)
        self.assertEqual(len(resultados), 2)
        self.assertTrue(all(r["cantidad"] > 0 for r in resultados))
        self.assertTrue(all(r["disponible"] is True for r in resultados))
        pares = {(r["codigo"], r["sucursal_codigo"]) for r in resultados}
        self.assertEqual(
            pares,
            {("DEMO-A", "DEMO-NORTE"), ("DEMO-B", "DEMO-SUR")},
        )

    def test_sucursal_y_solo_disponibles(self):
        resultados = self.filtrar(
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
        )
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["codigo"], "DEMO-A")
        self.assertEqual(resultados[0]["sucursal_codigo"], "DEMO-NORTE")
        self.assertEqual(resultados[0]["cantidad"], 5)

    def test_compatible_con_categoria(self):
        resultados = self.filtrar(
            sucursal="DEMO-NORTE",
            categoria="DEMO-X",
        )
        self.assertEqual(
            [r["codigo"] for r in resultados],
            ["DEMO-A", "DEMO-C"],
        )

    def test_compatible_con_busqueda_nombre(self):
        resultados = self.filtrar(
            sucursal="DEMO-SUR",
            solo_disponibles=True,
            busqueda="Producto demo B",
        )
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["codigo"], "DEMO-B")
        self.assertEqual(resultados[0]["cantidad"], 3)

    def test_compatible_con_todos_los_filtros(self):
        resultados = self.filtrar(
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
            categoria="DEMO-X",
            busqueda="demo A",
        )
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["codigo"], "DEMO-A")

    def test_informa_cuando_no_hay_resultados(self):
        respuesta = self.consultar(
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
            busqueda="Producto demo C",
        )
        self.assertTrue(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 0)
        self.assertEqual(respuesta["resultados"], [])
        self.assertEqual(respuesta["mensaje"], MENSAJE_SIN_RESULTADOS)

    def test_informa_cuando_si_hay_resultados(self):
        respuesta = self.consultar(
            sucursal="DEMO-SUR",
            solo_disponibles=True,
        )
        self.assertFalse(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 1)
        self.assertEqual(respuesta["resultados"][0]["codigo"], "DEMO-B")
        self.assertIn("1", respuesta["mensaje"])

    def test_limpiar_filtro_sucursal_vacia(self):
        resultados = self.filtrar(sucursal="")
        self.assertEqual(len(resultados), 6)


if __name__ == "__main__":
    unittest.main()
