import tempfile
import unittest

from pathlib import Path

from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar

from src.backend.repartidores_s3 import registrar_repartidor

from src.backend.entregas_s3 import (
    registrar_entrega,
    registrar_fecha_salida,
    registrar_fecha_entrega,
    obtener_historial_entrega,
    DatosEntregaInvalidos,
    EntregaNoEncontrada
)


class FechasEntregasS3Tests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.db = Path(self.temp.name) / "fechas.sqlite3"

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
                ("FECHAS-001", sucursal["id"], "PREPARADO")
            )

            self.pedido_id = cursor.lastrowid

        repartidor = registrar_repartidor(
            "REP-FECHAS-001",
            "Repartidor de prueba",
            self.db
        )

        entrega = registrar_entrega(
            self.pedido_id,
            repartidor["id"],
            db_path=self.db
        )

        self.entrega_id = entrega["id"]

    def test_registrar_fecha_salida(self):

        resultado = registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T10:00:00Z",
            self.db
        )

        self.assertEqual(
            resultado["fecha_salida"],
            "2026-11-05T10:00:00.000Z"
        )

    def test_no_permitir_salida_duplicada(self):

        registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T10:00:00Z",
            self.db
        )

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_fecha_salida(
                self.entrega_id,
                "2026-11-05T11:00:00Z",
                self.db
            )

    def test_no_permitir_recepcion_sin_salida(self):

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_fecha_entrega(
                self.entrega_id,
                "2026-11-05T11:00:00Z",
                self.db
            )

    def test_registrar_fecha_recepcion(self):

        registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T10:00:00Z",
            self.db
        )

        resultado = registrar_fecha_entrega(
            self.entrega_id,
            "2026-11-05T11:00:00Z",
            self.db
        )

        self.assertEqual(
            resultado["fecha_entrega"],
            "2026-11-05T11:00:00.000Z"
        )

    def test_rechazar_recepcion_anterior_a_salida(self):

        registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T12:00:00Z",
            self.db
        )

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_fecha_entrega(
                self.entrega_id,
                "2026-11-05T10:00:00Z",
                self.db
            )

    def test_no_permitir_recepcion_duplicada(self):

        registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T10:00:00Z",
            self.db
        )

        registrar_fecha_entrega(
            self.entrega_id,
            "2026-11-05T11:00:00Z",
            self.db
        )

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_fecha_entrega(
                self.entrega_id,
                "2026-11-05T12:00:00Z",
                self.db
            )

    def test_historial_entrega(self):

        registrar_fecha_salida(
            self.entrega_id,
            "2026-11-05T10:00:00Z",
            self.db
        )

        registrar_fecha_entrega(
            self.entrega_id,
            "2026-11-05T11:00:00Z",
            self.db
        )

        historial = obtener_historial_entrega(
            self.entrega_id,
            self.db
        )

        tipos = [evento["tipo"] for evento in historial]

        self.assertIn("ENTREGA_ASIGNADA", tipos)
        self.assertIn("SALIDA_REPARTIDOR", tipos)
        self.assertIn("RECEPCION_CONFIRMADA", tipos)
        self.assertIn("ESTADO_PEDIDO", tipos)

    def test_entrega_inexistente(self):

        with self.assertRaises(EntregaNoEncontrada):
            registrar_fecha_salida(
                99999,
                db_path=self.db
            )

    def test_rechazar_fecha_sin_zona_horaria(self):

        with self.assertRaises(DatosEntregaInvalidos):
            registrar_fecha_salida(
                self.entrega_id,
                "2026-11-05T10:00:00",
                self.db
            )


if __name__ == "__main__":
    unittest.main()
