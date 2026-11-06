import tempfile
import unittest

from pathlib import Path

from src.database.database import (
    initialize_database,
    connect_database
)

from src.database.migrate_josue import migrar

from src.backend.repartidores_s3 import registrar_repartidor, actualizar_repartidor

from src.backend.entregas_s3 import (
    registrar_entrega,
    obtener_entrega,
    listar_entregas,
    obtener_historial_pedido,
    PedidoNoEncontrado,
    RepartidorNoDisponible,
    EntregaDuplicada,
    DatosEntregaInvalidos
)


class EntregasS3Tests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.db = Path(self.temp.name) / "entregas.sqlite3"

        initialize_database(self.db, demo=True)
        migrar(self.db)

        with connect_database(self.db) as db:
            sucursal = db.execute(
                "SELECT id FROM sucursales WHERE codigo = 'DEMO-NORTE'"
            ).fetchone()

            cursor = db.execute(
                """
                INSERT INTO pedidos(codigo, sucursal_id, estado)
                VALUES (?, ?, ?)
                """,
                ("TEST-PEDIDO-001", sucursal["id"], "PREPARADO")
            )

            self.pedido_id = cursor.lastrowid

        repartidor = registrar_repartidor(
            "REP-TEST-001",
            "Repartidor de prueba",
            self.db
        )

        self.repartidor_id = repartidor["id"]

    def test_registrar_entrega(self):
        resultado = registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            db_path=self.db
        )

        self.assertEqual(resultado["pedido_id"], self.pedido_id)
        self.assertEqual(resultado["repartidor_id"], self.repartidor_id)
        self.assertEqual(resultado["estado_entrega"], "ASIGNADA")
        self.assertIsNotNone(resultado["fecha_asignacion"])

    def test_registrar_entrega_con_observaciones(self):
        resultado = registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            "Entrega de prueba",
            self.db
        )

        self.assertEqual(
            resultado["observaciones"],
            "Entrega de prueba"
        )

    def test_pedido_inexistente(self):
        with self.assertRaises(PedidoNoEncontrado):
            registrar_entrega(
                99999,
                self.repartidor_id,
                db_path=self.db
            )

    def test_repartidor_inexistente(self):
        with self.assertRaises(RepartidorNoDisponible):
            registrar_entrega(
                self.pedido_id,
                99999,
                db_path=self.db
            )

    def test_repartidor_inactivo(self):
        actualizar_repartidor(
            self.repartidor_id,
            activo=False,
            db_path=self.db
        )

        with self.assertRaises(RepartidorNoDisponible):
            registrar_entrega(
                self.pedido_id,
                self.repartidor_id,
                db_path=self.db
            )

    def test_no_permite_dos_entregas_para_un_pedido(self):
        registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            db_path=self.db
        )

        with self.assertRaises(EntregaDuplicada):
            registrar_entrega(
                self.pedido_id,
                self.repartidor_id,
                db_path=self.db
            )

    def test_consultar_entrega(self):
        nueva = registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            db_path=self.db
        )

        resultado = obtener_entrega(
            nueva["id"],
            self.db
        )

        self.assertEqual(resultado["pedido_id"], self.pedido_id)
        self.assertEqual(resultado["repartidor_nombre"], "Repartidor de prueba")

    def test_listar_entregas(self):
        registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            db_path=self.db
        )

        resultado = listar_entregas(db_path=self.db)

        self.assertEqual(len(resultado), 1)

    def test_filtrar_entregas_por_estado(self):
        registrar_entrega(
            self.pedido_id,
            self.repartidor_id,
            db_path=self.db
        )

        resultado = listar_entregas(
            estado="ASIGNADA",
            db_path=self.db
        )

        self.assertEqual(len(resultado), 1)

    def test_consultar_historial_pedido(self):
        historial = obtener_historial_pedido(
            self.pedido_id,
            self.db
        )

        self.assertGreaterEqual(len(historial), 1)
        self.assertEqual(
            historial[0]["estado_nuevo"],
            "PREPARADO"
        )

    def test_no_asignar_pedido_cancelado(self):
        with connect_database(self.db) as db:
            db.execute(
                "UPDATE pedidos SET estado = 'CANCELADO' WHERE id = ?",
                (self.pedido_id,)
            )

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_entrega(
                self.pedido_id,
                self.repartidor_id,
                db_path=self.db
            )


if __name__ == "__main__":
    unittest.main()
