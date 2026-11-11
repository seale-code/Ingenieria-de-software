"""Pruebas unitarias para la gestion de preparacion de pedidos (S3-01 / Issue #16)."""

import tempfile
import unittest
from pathlib import Path

from src.backend.pedidos_s2 import iniciar_modulo, registrar_pedido
from src.backend.preparacion_pedidos import (
    ErrorPreparacionPedido,
    PedidoNoEncontrado,
    TransicionPreparacionInvalida,
    completar_preparacion_pedido,
    consultar_pedidos_asignados,
    iniciar_preparacion_pedido,
    obtener_pedido_preparacion,
    registrar_avance_preparacion,
)
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class TestPreparacionPedidos(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "prueba_s3_preparacion.sqlite3"

        initialize_database(self.db_path, demo=True)
        migrar(self.db_path, hasta=3)
        iniciar_modulo(self.db_path)

        self.pedido_norte = registrar_pedido(
            {
                "cliente": "Ana Torres",
                "latitud": -12.005,
                "longitud": -77.050,
                "items": [{"producto_codigo": "DEMO-A", "cantidad": 2}],
            },
            db_path=self.db_path,
        )
        self.pedido_sur = registrar_pedido(
            {
                "cliente": "Luis Gomez",
                "latitud": -12.095,
                "longitud": -77.030,
                "items": [{"producto_codigo": "DEMO-B", "cantidad": 1}],
            },
            db_path=self.db_path,
        )

    def test_consultar_pedidos_asignados_por_sucursal(self):
        norte = consultar_pedidos_asignados(
            sucursal_codigo="DEMO-NORTE",
            db_path=self.db_path,
        )
        self.assertEqual(len(norte), 1)
        self.assertEqual(norte[0]["pedido_id"], self.pedido_norte["pedido_id"])
        self.assertEqual(norte[0]["sucursal_codigo"], "DEMO-NORTE")
        self.assertEqual(norte[0]["estado"], "ASIGNADO")
        self.assertEqual(norte[0]["items"][0]["producto_codigo"], "DEMO-A")
        self.assertEqual(norte[0]["items"][0]["cantidad"], 2)

        sur = consultar_pedidos_asignados(
            sucursal_codigo="DEMO-SUR",
            db_path=self.db_path,
        )
        self.assertEqual(len(sur), 1)
        self.assertEqual(sur[0]["pedido_id"], self.pedido_sur["pedido_id"])
        self.assertEqual(sur[0]["sucursal_codigo"], "DEMO-SUR")

    def test_flujo_completo_preparacion_valido_y_registro_historial(self):
        pid = self.pedido_norte["pedido_id"]

        paso_1 = iniciar_preparacion_pedido(pid, db_path=self.db_path)
        self.assertEqual(paso_1["estado_anterior"], "ASIGNADO")
        self.assertEqual(paso_1["estado_nuevo"], "EN_PREPARACION")
        self.assertEqual(paso_1["pedido"]["estado"], "EN_PREPARACION")

        paso_2 = completar_preparacion_pedido(pid, db_path=self.db_path)
        self.assertEqual(paso_2["estado_anterior"], "EN_PREPARACION")
        self.assertEqual(paso_2["estado_nuevo"], "PREPARADO")
        self.assertEqual(paso_2["pedido"]["estado"], "PREPARADO")

        transiciones = [
            (h["estado_anterior"], h["estado_nuevo"])
            for h in paso_2["pedido"]["historial"]
        ]
        self.assertEqual(
            transiciones,
            [
                (None, "ASIGNADO"),
                ("ASIGNADO", "EN_PREPARACION"),
                ("EN_PREPARACION", "PREPARADO"),
            ],
        )

    def test_consultar_pedidos_filtrando_por_estado(self):
        pid_norte = self.pedido_norte["pedido_id"]
        iniciar_preparacion_pedido(pid_norte, db_path=self.db_path)

        en_prep = consultar_pedidos_asignados(
            estado="EN_PREPARACION",
            db_path=self.db_path,
        )
        self.assertEqual([p["pedido_id"] for p in en_prep], [pid_norte])

        asignados = consultar_pedidos_asignados(
            estado="ASIGNADO",
            db_path=self.db_path,
        )
        self.assertEqual(
            [p["pedido_id"] for p in asignados],
            [self.pedido_sur["pedido_id"]],
        )

    def test_excluir_preparados_en_bandeja_pendientes(self):
        pid_norte = self.pedido_norte["pedido_id"]
        iniciar_preparacion_pedido(pid_norte, db_path=self.db_path)
        completar_preparacion_pedido(pid_norte, db_path=self.db_path)

        pendientes = consultar_pedidos_asignados(
            incluir_preparados=False,
            db_path=self.db_path,
        )
        self.assertEqual(
            [p["pedido_id"] for p in pendientes],
            [self.pedido_sur["pedido_id"]],
        )

    def test_rechaza_pasar_directamente_de_asignado_a_preparado(self):
        pid = self.pedido_norte["pedido_id"]
        with self.assertRaises(TransicionPreparacionInvalida):
            completar_preparacion_pedido(pid, db_path=self.db_path)

        actual = obtener_pedido_preparacion(pid, db_path=self.db_path)
        self.assertEqual(actual["estado"], "ASIGNADO")

    def test_rechaza_retroceder_de_preparado_a_en_preparacion(self):
        pid = self.pedido_norte["pedido_id"]
        iniciar_preparacion_pedido(pid, db_path=self.db_path)
        completar_preparacion_pedido(pid, db_path=self.db_path)

        with self.assertRaises(TransicionPreparacionInvalida):
            iniciar_preparacion_pedido(pid, db_path=self.db_path)

    def test_rechaza_preparar_pedido_cancelado_o_entregado(self):
        pid = self.pedido_norte["pedido_id"]
        with connect_database(self.db_path) as db:
            db.execute("UPDATE pedidos SET estado = 'CANCELADO' WHERE id = ?", (pid,))

        with self.assertRaises(TransicionPreparacionInvalida):
            iniciar_preparacion_pedido(pid, db_path=self.db_path)

    def test_rechaza_estado_destino_ajeno_a_preparacion(self):
        pid = self.pedido_norte["pedido_id"]
        with self.assertRaises(TransicionPreparacionInvalida):
            registrar_avance_preparacion(pid, "ENTREGADO", db_path=self.db_path)

    def test_pedido_inexistente_lanza_error_claro(self):
        with self.assertRaises(PedidoNoEncontrado):
            iniciar_preparacion_pedido(99999, db_path=self.db_path)

    def test_rechaza_preparar_pedido_sin_detalles(self):
        with connect_database(self.db_path) as db:
            sucursal_id = db.execute(
                "SELECT id FROM sucursales WHERE codigo = 'DEMO-NORTE'"
            ).fetchone()[0]
            cursor = db.execute(
                "INSERT INTO pedidos(codigo, sucursal_id, estado) VALUES ('PED-VACIO', ?, 'ASIGNADO')",
                (sucursal_id,),
            )
            pedido_vacio_id = cursor.lastrowid

        with self.assertRaises(ErrorPreparacionPedido):
            iniciar_preparacion_pedido(pedido_vacio_id, db_path=self.db_path)

    def test_validaciones_de_parametros_invalidos(self):
        with self.assertRaises(ErrorPreparacionPedido):
            obtener_pedido_preparacion(0, db_path=self.db_path)
        with self.assertRaises(ErrorPreparacionPedido):
            consultar_pedidos_asignados(estado="ESTADO_INEXISTENTE", db_path=self.db_path)


if __name__ == "__main__":
    unittest.main()
