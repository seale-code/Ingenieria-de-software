import tempfile
import unittest

from pathlib import Path

from src.database.database import initialize_database
from src.database.migrate_josue import migrar

from src.backend.repartidores_s3 import (
    registrar_repartidor,
    listar_repartidores,
    obtener_repartidor,
    actualizar_repartidor,
    DatosInvalidos,
    RepartidorNoEncontrado
)


class RepartidoresS3Tests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.db = Path(self.temp.name) / "prueba.sqlite3"

        initialize_database(self.db)
        migrar(self.db)

    def test_registrar_repartidor(self):
        resultado = registrar_repartidor(
            "REP-001",
            "Josue Mogollon",
            self.db
        )

        self.assertEqual(resultado["codigo"], "REP-001")
        self.assertEqual(resultado["nombre"], "Josue Mogollon")
        self.assertEqual(resultado["activo"], 1)

    def test_rechazar_codigo_duplicado(self):
        registrar_repartidor(
            "REP-001",
            "Primer repartidor",
            self.db
        )

        with self.assertRaises(DatosInvalidos):
            registrar_repartidor(
                "REP-001",
                "Segundo repartidor",
                self.db
            )

    def test_rechazar_nombre_vacio(self):
        with self.assertRaises(DatosInvalidos):
            registrar_repartidor(
                "REP-002",
                "   ",
                self.db
            )

    def test_listar_repartidores(self):
        registrar_repartidor(
            "REP-001",
            "Josue",
            self.db
        )

        resultado = listar_repartidores(db_path=self.db)

        self.assertEqual(len(resultado), 1)

    def test_consultar_repartidor(self):
        nuevo = registrar_repartidor(
            "REP-001",
            "Josue",
            self.db
        )

        resultado = obtener_repartidor(
            nuevo["id"],
            self.db
        )

        self.assertEqual(resultado["codigo"], "REP-001")

    def test_actualizar_repartidor(self):
        nuevo = registrar_repartidor(
            "REP-001",
            "Josue",
            self.db
        )

        resultado = actualizar_repartidor(
            nuevo["id"],
            nombre="Josue Mogollon",
            activo=False,
            db_path=self.db
        )

        self.assertEqual(resultado["nombre"], "Josue Mogollon")
        self.assertEqual(resultado["activo"], 0)

    def test_filtrar_repartidores_activos(self):
        nuevo = registrar_repartidor(
            "REP-001",
            "Josue",
            self.db
        )

        actualizar_repartidor(
            nuevo["id"],
            activo=False,
            db_path=self.db
        )

        resultado = listar_repartidores(
            activo=True,
            db_path=self.db
        )

        self.assertEqual(len(resultado), 0)

    def test_repartidor_inexistente(self):
        with self.assertRaises(RepartidorNoEncontrado):
            actualizar_repartidor(
                999,
                nombre="Inexistente",
                db_path=self.db
            )


if __name__ == "__main__":
    unittest.main()
