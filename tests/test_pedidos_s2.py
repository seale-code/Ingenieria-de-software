"""Pruebas unitarias y de integración contra el esquema real del Sprint 1."""

import concurrent.futures
from pathlib import Path
import sqlite3
import tempfile
import unittest

from src.database.database import connect_database, initialize_database
from src.backend.asignacion_sucursal import distancia_km, ordenar_candidatas
from src.backend.pedidos_s2 import (
    DatosInvalidos, ModuloNoInicializado, configurar_capacidad, iniciar_modulo,
    obtener_pedido, registrar_pedido,
)


def solicitud(codigo="DEMO-A", cantidad=2, lat=-12.0, lon=-77.05):
    return {"cliente": "Cliente de prueba", "latitud": lat, "longitud": lon,
            "items": [{"producto_codigo": codigo, "cantidad": cantidad}]}


class PedidosS2Test(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.db = Path(self.temporal.name) / "test.sqlite3"
        initialize_database(self.db, demo=True)
        iniciar_modulo(self.db)
        configurar_capacidad("DEMO-NORTE", 3, self.db)
        configurar_capacidad("DEMO-SUR", 3, self.db)

    def stock(self, codigo, sucursal):
        with connect_database(self.db, read_only=True) as db:
            return db.execute("""
                SELECT i.cantidad FROM inventario i
                JOIN productos p ON p.id=i.producto_id
                JOIN sucursales s ON s.id=i.sucursal_id
                WHERE p.codigo=? AND s.codigo=?
            """, (codigo, sucursal)).fetchone()[0]

    def total(self, tabla):
        # Solo nombres constantes definidos en las pruebas.
        self.assertIn(tabla, ("s2_pedidos", "s2_pedido_detalles", "s2_reservas"))
        with connect_database(self.db, read_only=True) as db:
            return db.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]

    def test_01_pedido_valido_y_reserva(self):
        respuesta = registrar_pedido(solicitud(), self.db)
        self.assertEqual(respuesta["estado"], "ASIGNADO")
        self.assertEqual(respuesta["sucursal_codigo"], "DEMO-NORTE")
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 3)
        self.assertEqual(self.total("s2_reservas"), 1)
        self.assertEqual(obtener_pedido(respuesta["pedido_id"], self.db)["items"][0]["reservada"], 1)

    def test_02_elige_sucursal_que_tiene_producto(self):
        respuesta = registrar_pedido(solicitud("DEMO-B", 1), self.db)
        self.assertEqual(respuesta["sucursal_codigo"], "DEMO-SUR")
        self.assertEqual(self.stock("DEMO-B", "DEMO-SUR"), 2)

    def test_03_sin_stock_persistido_sin_reservar(self):
        respuesta = registrar_pedido(solicitud("DEMO-C", 1), self.db)
        self.assertEqual(respuesta["estado"], "SIN_ASIGNAR")
        self.assertIsNone(respuesta["sucursal_codigo"])
        self.assertTrue(respuesta["motivo"])
        self.assertEqual(self.total("s2_pedidos"), 1)
        self.assertEqual(self.total("s2_pedido_detalles"), 1)
        self.assertEqual(self.total("s2_reservas"), 0)

    def test_04_stock_parcial_no_hace_reservas(self):
        datos = solicitud("DEMO-A", 1)
        datos["items"].append({"producto_codigo": "DEMO-B", "cantidad": 1})
        self.assertEqual(registrar_pedido(datos, self.db)["estado"], "SIN_ASIGNAR")
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 5)
        self.assertEqual(self.stock("DEMO-B", "DEMO-SUR"), 3)

    def test_05_capacidad_agotada(self):
        configurar_capacidad("DEMO-NORTE", 1, self.db)
        self.assertEqual(registrar_pedido(solicitud("DEMO-A", 1), self.db)["estado"], "ASIGNADO")
        self.assertEqual(registrar_pedido(solicitud("DEMO-A", 1), self.db)["estado"], "SIN_ASIGNAR")
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 4)

    def test_06_capacidad_cero(self):
        configurar_capacidad("DEMO-NORTE", 0, self.db)
        self.assertEqual(registrar_pedido(solicitud(), self.db)["estado"], "SIN_ASIGNAR")

    def test_07_cantidad_invalidada_antes_de_insertar(self):
        for cantidad in (0, -3, 1.5, True, "2", 10001):
            with self.subTest(cantidad=cantidad), self.assertRaises(DatosInvalidos):
                registrar_pedido(solicitud(cantidad=cantidad), self.db)
        self.assertEqual(self.total("s2_pedidos"), 0)

    def test_08_codigo_inexistente(self):
        with self.assertRaisesRegex(DatosInvalidos, "inexistentes"):
            registrar_pedido(solicitud("NO-EXISTE"), self.db)
        self.assertEqual(self.total("s2_pedidos"), 0)

    def test_09_cliente_vacio(self):
        datos = solicitud()
        datos["cliente"] = "  "
        with self.assertRaises(DatosInvalidos):
            registrar_pedido(datos, self.db)

    def test_10_coordenadas_invalidas(self):
        for lat, lon in ((91, 0), (0, -190), (float("nan"), 0), (True, 0)):
            with self.subTest(lat=lat, lon=lon), self.assertRaises(DatosInvalidos):
                registrar_pedido(solicitud(lat=lat, lon=lon), self.db)

    def test_11_lineas_duplicadas_se_agrupan(self):
        datos = solicitud("DEMO-A", 2)
        datos["items"].append({"producto_codigo": "DEMO-A", "cantidad": 2})
        respuesta = registrar_pedido(datos, self.db)
        self.assertEqual(respuesta["items"], [{"producto_codigo": "DEMO-A", "cantidad": 4}])
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 1)
        self.assertEqual(self.total("s2_pedido_detalles"), 1)

    def test_12_agregacion_no_sobrevende(self):
        datos = solicitud("DEMO-A", 3)
        datos["items"].append({"producto_codigo": "DEMO-A", "cantidad": 3})
        self.assertEqual(registrar_pedido(datos, self.db)["estado"], "SIN_ASIGNAR")
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 5)

    def test_13_operacion_atomica_revierte_si_falla_reserva(self):
        with connect_database(self.db) as db:
            db.execute("""
                CREATE TRIGGER impedir_reserva BEFORE INSERT ON s2_reservas
                BEGIN SELECT RAISE(ABORT, 'fallo intencional'); END
            """)
        with self.assertRaises(sqlite3.IntegrityError):
            registrar_pedido(solicitud(), self.db)
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 5)
        self.assertEqual(self.total("s2_pedidos"), 0)
        self.assertEqual(self.total("s2_pedido_detalles"), 0)

    def test_14_dos_pedidos_concurrentes_no_sobrevenden(self):
        with connect_database(self.db) as db:
            db.execute("""
                UPDATE inventario SET cantidad=1
                WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A')
                  AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')
            """)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as grupo:
            tareas = [grupo.submit(registrar_pedido, solicitud("DEMO-A", 1), self.db) for _ in range(2)]
            respuestas = [f.result() for f in tareas]
        self.assertEqual(sorted(x["estado"] for x in respuestas), ["ASIGNADO", "SIN_ASIGNAR"])
        self.assertEqual(self.stock("DEMO-A", "DEMO-NORTE"), 0)
        self.assertEqual(self.total("s2_reservas"), 1)
        self.assertEqual(self.total("s2_pedidos"), 2)

    def test_15_inicializacion_idempotente(self):
        registrar_pedido(solicitud(), self.db)
        iniciar_modulo(self.db)
        self.assertEqual(self.total("s2_pedidos"), 1)
        with connect_database(self.db, read_only=True) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_16_modulo_sin_inicializar(self):
        otra_db = Path(self.temporal.name) / "nueva.sqlite3"
        initialize_database(otra_db, demo=True)
        with self.assertRaises(ModuloNoInicializado):
            registrar_pedido(solicitud(), otra_db)

    def test_17_pedido_inexistente(self):
        self.assertIsNone(obtener_pedido(123, self.db))

    def test_18_sucursal_inexistente(self):
        with self.assertRaises(DatosInvalidos):
            configurar_capacidad("NO-EXISTE", 2, self.db)

    def test_19_distancia_y_desempate(self):
        self.assertAlmostEqual(distancia_km(0, 0, 0, 0), 0)
        self.assertTrue(110 < distancia_km(0, 0, 1, 0) < 112)
        candidatas = [
            {"codigo": "Z", "distancia_km": 2, "capacidad_libre": 2},
            {"codigo": "B", "distancia_km": 2, "capacidad_libre": 4},
            {"codigo": "A", "distancia_km": 2, "capacidad_libre": 4},
        ]
        self.assertEqual([x["codigo"] for x in ordenar_candidatas(candidatas)], ["A", "B", "Z"])

    def test_20_no_modifica_stock_en_sucursal_ajena(self):
        registrar_pedido(solicitud("DEMO-A", 1), self.db)
        self.assertEqual(self.stock("DEMO-B", "DEMO-SUR"), 3)
        self.assertEqual(self.stock("DEMO-A", "DEMO-SUR"), 0)


if __name__ == "__main__":
    unittest.main()
