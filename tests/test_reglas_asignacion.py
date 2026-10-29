"""Pruebas unitarias para las reglas de asignacion de sucursal (S2-01 / Issue #9)."""

import unittest

from src.backend.reglas_asignacion import (
    asignar_sucursal_pedido,
    calcular_distancia_km,
    evaluar_elegibilidad_sucursal,
)


class TestReglasAsignacion(unittest.TestCase):

    def setUp(self):
        self.sucursal_norte = {
            "codigo": "DEMO-NORTE",
            "nombre": "Sucursal demo Norte",
            "latitud": -12.000,
            "longitud": -77.050,
            "stock_disponible": {"DEMO-A": 5, "DEMO-B": 0, "DEMO-C": 0},
            "pedidos_activos": 2,
            "capacidad_maxima": 10,
        }
        self.sucursal_sur = {
            "codigo": "DEMO-SUR",
            "nombre": "Sucursal demo Sur",
            "latitud": -12.100,
            "longitud": -77.030,
            "stock_disponible": {"DEMO-A": 5, "DEMO-B": 3, "DEMO-C": 0},
            "pedidos_activos": 4,
            "capacidad_maxima": 10,
        }

    def test_asigna_sucursal_mas_cercana_cuando_ambas_son_elegibles(self):
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-A": 2},
            cliente_latitud=-12.010,
            cliente_longitud=-77.050,
        )
        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["sucursal_asignada"], "DEMO-NORTE")
        self.assertEqual(resultado["ranking_elegibles"], ["DEMO-NORTE", "DEMO-SUR"])

    def test_descarta_sucursal_cercana_sin_stock_y_asigna_siguiente(self):
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-B": 2},
            cliente_latitud=-12.005,
            cliente_longitud=-77.050,
        )
        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["sucursal_asignada"], "DEMO-SUR")

    def test_descarta_sucursal_por_stock_parcial_en_pedido_multiproducto(self):
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-A": 1, "DEMO-B": 1},
            cliente_latitud=-12.005,
            cliente_longitud=-77.050,
        )
        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["sucursal_asignada"], "DEMO-SUR")

    def test_descarta_sucursal_cercana_con_capacidad_agotada(self):
        self.sucursal_norte["pedidos_activos"] = 10
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-A": 1},
            cliente_latitud=-12.001,
            cliente_longitud=-77.050,
        )
        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["sucursal_asignada"], "DEMO-SUR")

    def test_desempate_nivel_1_mayor_capacidad_disponible(self):
        suc_1 = {
            **self.sucursal_norte,
            "codigo": "SUC-1",
            "pedidos_activos": 5,
            "capacidad_maxima": 10,
        }
        suc_2 = {
            **self.sucursal_norte,
            "codigo": "SUC-2",
            "pedidos_activos": 1,
            "capacidad_maxima": 10,
        }
        resultado = asignar_sucursal_pedido(
            sucursales=[suc_1, suc_2],
            items_solicitados={"DEMO-A": 2},
            cliente_latitud=-12.000,
            cliente_longitud=-77.050,
        )
        self.assertEqual(resultado["sucursal_asignada"], "SUC-2")

    def test_desempate_nivel_2_mayor_stock_disponible(self):
        suc_1 = {
            **self.sucursal_norte,
            "codigo": "SUC-1",
            "pedidos_activos": 3,
            "stock_disponible": {"DEMO-A": 4},
        }
        suc_2 = {
            **self.sucursal_norte,
            "codigo": "SUC-2",
            "pedidos_activos": 3,
            "stock_disponible": {"DEMO-A": 9},
        }
        resultado = asignar_sucursal_pedido(
            sucursales=[suc_1, suc_2],
            items_solicitados={"DEMO-A": 2},
            cliente_latitud=-12.000,
            cliente_longitud=-77.050,
        )
        self.assertEqual(resultado["sucursal_asignada"], "SUC-2")

    def test_desempate_nivel_3_orden_alfabetico_por_codigo(self):
        suc_b = {**self.sucursal_norte, "codigo": "SUC-B"}
        suc_a = {**self.sucursal_norte, "codigo": "SUC-A"}
        resultado = asignar_sucursal_pedido(
            sucursales=[suc_b, suc_a],
            items_solicitados={"DEMO-A": 1},
            cliente_latitud=-12.000,
            cliente_longitud=-77.050,
        )
        self.assertEqual(resultado["sucursal_asignada"], "SUC-A")

    def test_rechazo_cuando_ninguna_sucursal_tiene_stock(self):
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-C": 1},
            cliente_latitud=-12.050,
            cliente_longitud=-77.040,
        )
        self.assertFalse(resultado["asignada"])
        self.assertIsNone(resultado["sucursal_asignada"])
        self.assertEqual(resultado["motivo_rechazo"], "SIN_STOCK_DISPONIBLE")

    def test_rechazo_cuando_sucursales_con_stock_no_tienen_capacidad(self):
        self.sucursal_norte["pedidos_activos"] = 10
        self.sucursal_sur["pedidos_activos"] = 10
        resultado = asignar_sucursal_pedido(
            sucursales=[self.sucursal_norte, self.sucursal_sur],
            items_solicitados={"DEMO-A": 1},
            cliente_latitud=-12.050,
            cliente_longitud=-77.040,
        )
        self.assertFalse(resultado["asignada"])
        self.assertIsNone(resultado["sucursal_asignada"])
        self.assertEqual(resultado["motivo_rechazo"], "SIN_CAPACIDAD_DISPONIBLE")

    def test_rechazo_cuando_lista_de_sucursales_esta_vacia(self):
        resultado = asignar_sucursal_pedido(
            sucursales=[],
            items_solicitados={"DEMO-A": 1},
            cliente_latitud=-12.050,
            cliente_longitud=-77.040,
        )
        self.assertFalse(resultado["asignada"])
        self.assertEqual(resultado["motivo_rechazo"], "SIN_SUCURSALES_REGISTRADAS")

    def test_calculo_distancia_haversine_mismo_punto_es_cero(self):
        self.assertEqual(
            calcular_distancia_km(-12.000, -77.050, -12.000, -77.050),
            0.0,
        )

    def test_validaciones_rechazan_coordenadas_o_cantidades_invalidas(self):
        with self.assertRaises(ValueError):
            calcular_distancia_km(-95.0, -77.0, -12.0, -77.0)
        with self.assertRaises(ValueError):
            evaluar_elegibilidad_sucursal(
                self.sucursal_norte, {"DEMO-A": 0}, -12.0, -77.0
            )
        with self.assertRaises(ValueError):
            evaluar_elegibilidad_sucursal(
                self.sucursal_norte, {}, -12.0, -77.0
            )


if __name__ == "__main__":
    unittest.main()
