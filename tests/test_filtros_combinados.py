"""Pruebas unitarias para validar filtros combinados con búsqueda (S1-03 / Issue #8)."""

import tempfile
import unittest
from pathlib import Path

from src.backend.filtro_sucursal_stock import MENSAJE_SIN_RESULTADOS
from src.backend.filtros_combinados import validar_y_filtrar_catalogo
from src.database.database import initialize_database


class TestFiltrosCombinados(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "prueba_combinados.sqlite3"
        initialize_database(self.db_path, demo=True)

    def consultar(
        self,
        busqueda="",
        categoria=None,
        sucursal=None,
        solo_disponibles=False,
    ):
        return validar_y_filtrar_catalogo(
            busqueda=busqueda,
            categoria=categoria,
            sucursal=sucursal,
            solo_disponibles=solo_disponibles,
            db_path=self.db_path,
        )

    def test_s1_cp_07_busqueda_b_categoria_y_sur_disponibles_encuentra_b(self):
        """S1-CP-07 (parte 1): Buscar B con categoría Y y sucursal Sur, solo disponibles -> Mostrar B."""
        respuesta = self.consultar(
            busqueda="Producto demo B",
            categoria="DEMO-Y",
            sucursal="DEMO-SUR",
            solo_disponibles=True,
        )
        self.assertFalse(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 1)
        producto = respuesta["resultados"][0]
        self.assertEqual(producto["codigo"], "DEMO-B")
        self.assertEqual(producto["categoria_codigo"], "DEMO-Y")
        self.assertEqual(producto["sucursal_codigo"], "DEMO-SUR")
        self.assertEqual(producto["cantidad"], 3)

    def test_s1_cp_07_busqueda_b_categoria_x_sur_disponibles_sin_resultados(self):
        """S1-CP-07 (parte 2): Buscar B con categoría X y sucursal Sur, solo disponibles -> Sin resultados."""
        respuesta = self.consultar(
            busqueda="Producto demo B",
            categoria="DEMO-X",
            sucursal="DEMO-SUR",
            solo_disponibles=True,
        )
        self.assertTrue(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 0)
        self.assertEqual(respuesta["resultados"], [])
        self.assertEqual(respuesta["mensaje"], MENSAJE_SIN_RESULTADOS)

    def test_s1_cp_05_filtrar_categoria_x_y_luego_limpiar_recupera_demas_filtros(self):
        """S1-CP-05: Elegir categoría X y luego limpiar el filtro conservando sucursal Norte."""
        con_categoria = self.consultar(
            categoria="DEMO-X",
            sucursal="DEMO-NORTE",
        )
        self.assertEqual(
            [r["codigo"] for r in con_categoria["resultados"]],
            ["DEMO-A", "DEMO-C"],
        )

        limpiando_categoria = self.consultar(
            categoria="",
            sucursal="DEMO-NORTE",
        )
        self.assertEqual(
            [r["codigo"] for r in limpiando_categoria["resultados"]],
            ["DEMO-A", "DEMO-B", "DEMO-C"],
        )

    def test_s1_cp_06_elegir_norte_y_solo_disponibles_incluye_a_excluye_b_c(self):
        """S1-CP-06: Elegir Norte y activar solo disponibles -> Incluir A; excluir B y C."""
        respuesta = self.consultar(
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
        )
        self.assertFalse(respuesta["sin_resultados"])
        self.assertEqual(
            [r["codigo"] for r in respuesta["resultados"]],
            ["DEMO-A"],
        )

    def test_busqueda_parcial_minusculas_combinada_con_filtros(self):
        respuesta = self.consultar(
            busqueda="demo a",
            categoria="DEMO-X",
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
        )
        self.assertFalse(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 1)
        self.assertEqual(respuesta["resultados"][0]["codigo"], "DEMO-A")

    def test_busqueda_inexistente_con_filtros_muestra_mensaje_sin_resultados(self):
        respuesta = self.consultar(
            busqueda="Medicamento Inexistente XYZ",
            categoria="DEMO-X",
            sucursal="DEMO-NORTE",
            solo_disponibles=True,
        )
        self.assertTrue(respuesta["sin_resultados"])
        self.assertEqual(respuesta["resultados"], [])
        self.assertEqual(respuesta["mensaje"], MENSAJE_SIN_RESULTADOS)

    def test_espacios_en_blanco_se_normalizan_correctamente(self):
        respuesta = self.consultar(
            busqueda="  Producto demo A  ",
            categoria="  DEMO-X  ",
            sucursal="  DEMO-NORTE  ",
            solo_disponibles=True,
        )
        self.assertFalse(respuesta["sin_resultados"])
        self.assertEqual(respuesta["total"], 1)
        self.assertEqual(respuesta["resultados"][0]["codigo"], "DEMO-A")

    def test_caracteres_sql_en_busqueda_combinada_se_tratan_como_texto(self):
        respuesta = self.consultar(
            busqueda="' OR 1=1 --",
            categoria="DEMO-X",
            sucursal="DEMO-NORTE",
        )
        self.assertTrue(respuesta["sin_resultados"])
        self.assertEqual(respuesta["resultados"], [])
        self.assertEqual(respuesta["mensaje"], MENSAJE_SIN_RESULTADOS)

    def test_validacion_rechaza_tipos_invalidos_en_parametros(self):
        with self.assertRaises(ValueError):
            self.consultar(busqueda=123)
        with self.assertRaises(ValueError):
            self.consultar(categoria=456)
        with self.assertRaises(ValueError):
            self.consultar(sucursal=789)
        with self.assertRaises(ValueError):
            self.consultar(solo_disponibles="si")

    def test_registro_de_filtros_aplicados_en_respuesta(self):
        respuesta = self.consultar(
            busqueda=" demo B ",
            categoria=" DEMO-Y ",
            sucursal=" DEMO-SUR ",
            solo_disponibles=True,
        )
        self.assertEqual(
            respuesta["filtros_aplicados"],
            {
                "busqueda": "demo B",
                "categoria": "DEMO-Y",
                "sucursal": "DEMO-SUR",
                "solo_disponibles": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
