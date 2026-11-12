"""Pruebas del módulo S3-04 sobre una base SQLite temporal."""

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
)
from src.backend.soporte_pedidos_s3 import (
    actualizar_estado_incidencia,
    cancelar_pedido,
    cambiar_estado_pedido,
    listar_incidencias,
    obtener_historial_pedido,
    obtener_incidencia,
    registrar_incidencia,
    DatosIncidenciaInvalidos,
    ErrorSoportePedido,
    IncidenciaNoEncontrada,
    PermisoDenegado,
    TransicionIncidenciaInvalida,
    TransicionPedidoInvalida,
)


class SoportePedidosS3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "soporte_s3.sqlite3"

        initialize_database(self.db_path, demo=True)
        migrar(self.db_path, hasta=4)

        with connect_database(self.db_path) as db:
            self.sucursal_id = db.execute(
                "SELECT id FROM sucursales WHERE codigo='DEMO-NORTE'"
            ).fetchone()["id"]

            self.producto_id = db.execute(
                "SELECT id FROM productos WHERE codigo='DEMO-A'"
            ).fetchone()["id"]

        self.pedido_id = self.crear_pedido("S3-TEST-001", "PREPARADO")
        self.repartidor = registrar_repartidor(
            "REP-S3-001", "Repartidor de prueba", self.db_path
        )
        self.entrega = registrar_entrega(
            self.pedido_id, self.repartidor["id"], db_path=self.db_path
        )

    def crear_pedido(self, codigo, estado="ASIGNADO"):
        with connect_database(self.db_path) as db:
            cursor = db.execute(
                """
                INSERT INTO pedidos(codigo, sucursal_id, estado)
                VALUES (?, ?, ?)
                """,
                (codigo, self.sucursal_id, estado),
            )
            return cursor.lastrowid

    def crear_reserva(self, pedido_id, cantidad=2):
        with connect_database(self.db_path) as db:
            detalle = db.execute(
                """
                INSERT INTO detalles_pedido(pedido_id, producto_id, cantidad)
                VALUES (?, ?, ?)
                """,
                (pedido_id, self.producto_id, cantidad),
            )
            db.execute(
                """
                INSERT INTO reservas_stock(pedido_id, producto_id, sucursal_id, cantidad)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, self.producto_id, self.sucursal_id, cantidad),
            )
            return detalle.lastrowid

    def test_migracion_crea_tabla_de_incidencias_y_version_4(self):
        with connect_database(self.db_path, read_only=True) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)
            existe = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='incidencias_pedido'"
            ).fetchone()
            self.assertIsNotNone(existe)

    def test_repartidor_no_puede_salir_sin_fecha_registrada(self):
        with self.assertRaises(TransicionPedidoInvalida):
            cambiar_estado_pedido(
                self.pedido_id, "EN_CAMINO", "REPARTIDOR",
                self.repartidor["id"], self.db_path
            )

    def test_solo_repartidor_asignado_puede_iniciar_reparto(self):
        otro = registrar_repartidor("REP-S3-002", "Otro repartidor", self.db_path)
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)

        with self.assertRaises(PermisoDenegado):
            cambiar_estado_pedido(
                self.pedido_id, "EN_CAMINO", "REPARTIDOR",
                otro["id"], self.db_path
            )

    def test_asesor_no_puede_cambiar_estado_de_reparto(self):
        with self.assertRaises(PermisoDenegado):
            cambiar_estado_pedido(
                self.pedido_id, "EN_CAMINO", "ASESOR",
                1, self.db_path
            )

    def test_repartidor_inicia_reparto_y_sincroniza_entrega(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        resultado = cambiar_estado_pedido(
            self.pedido_id, "EN_CAMINO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        self.assertEqual(resultado["estado_nuevo"], "EN_CAMINO")
        self.assertEqual(resultado["estado_entrega"], "EN_CAMINO")
        with connect_database(self.db_path, read_only=True) as db:
            self.assertEqual(
                db.execute("SELECT estado FROM pedidos WHERE id=?", (self.pedido_id,)).fetchone()[0],
                "EN_CAMINO",
            )
            self.assertEqual(
                db.execute("SELECT estado FROM entregas WHERE id=?", (self.entrega["id"],)).fetchone()[0],
                "EN_CAMINO",
            )

    def test_consumo_de_reserva_al_salir_y_no_se_descuenta_dos_veces(self):
        pedido = self.crear_pedido("S3-CONSUME-001", "PREPARADO")
        self.crear_reserva(pedido, 2)
        repartidor = registrar_repartidor(
            "REP-CONSUME-001", "Repartidor consumo", self.db_path
        )
        entrega = registrar_entrega(pedido, repartidor["id"], db_path=self.db_path)

        registrar_fecha_salida(entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        salida = cambiar_estado_pedido(
            pedido, "EN_CAMINO", "REPARTIDOR", repartidor["id"], self.db_path
        )
        self.assertEqual(salida["reservas_consumidas"], 1)
        with connect_database(self.db_path, read_only=True) as db:
            self.assertEqual(
                db.execute(
                    "SELECT cantidad FROM inventario WHERE producto_id=? AND sucursal_id=?",
                    (self.producto_id, self.sucursal_id),
                ).fetchone()[0],
                3,
            )
            self.assertEqual(
                db.execute(
                    "SELECT estado FROM reservas_stock WHERE pedido_id=?", (pedido,)
                ).fetchone()[0],
                "CONSUMIDA",
            )

        registrar_fecha_entrega(entrega["id"], "2026-11-12T11:00:00Z", self.db_path)
        entrega_final = cambiar_estado_pedido(
            pedido, "ENTREGADO", "REPARTIDOR", repartidor["id"], self.db_path
        )
        self.assertEqual(entrega_final["reservas_consumidas"], 0)
        with connect_database(self.db_path, read_only=True) as db:
            self.assertEqual(
                db.execute(
                    "SELECT cantidad FROM inventario WHERE producto_id=? AND sucursal_id=?",
                    (self.producto_id, self.sucursal_id),
                ).fetchone()[0],
                3,
            )

    def test_repartidor_confirma_entrega_solo_con_fecha_de_recepcion(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "EN_CAMINO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        with self.assertRaises(TransicionPedidoInvalida):
            cambiar_estado_pedido(
                self.pedido_id, "ENTREGADO", "REPARTIDOR",
                self.repartidor["id"], self.db_path
            )

        registrar_fecha_entrega(self.entrega["id"], "2026-11-12T11:00:00Z", self.db_path)
        resultado = cambiar_estado_pedido(
            self.pedido_id, "ENTREGADO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        self.assertEqual(resultado["estado_nuevo"], "ENTREGADO")
        self.assertEqual(resultado["estado_entrega"], "ENTREGADA")

    def test_historial_registra_transiciones_de_reparto(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "EN_CAMINO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        registrar_fecha_entrega(self.entrega["id"], "2026-11-12T11:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "ENTREGADO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        estados = [x["estado_nuevo"] for x in obtener_historial_pedido(self.pedido_id, self.db_path)]
        self.assertEqual(estados[-2:], ["EN_CAMINO", "ENTREGADO"])

    def test_administrador_cancela_pedido_y_libera_reserva(self):
        pedido = self.crear_pedido("S3-CANCEL-001", "ASIGNADO")
        self.crear_reserva(pedido, 2)
        resultado = cancelar_pedido(pedido, "ADMINISTRADOR", 7, self.db_path)
        self.assertEqual(resultado["estado_nuevo"], "CANCELADO")
        self.assertEqual(resultado["reservas_liberadas"], 1)
        with connect_database(self.db_path, read_only=True) as db:
            self.assertEqual(
                db.execute(
                    "SELECT cantidad FROM inventario WHERE producto_id=? AND sucursal_id=?",
                    (self.producto_id, self.sucursal_id),
                ).fetchone()[0],
                5,
            )
            reserva = db.execute(
                "SELECT estado, fecha_cierre FROM reservas_stock WHERE pedido_id=?",
                (pedido,),
            ).fetchone()
            self.assertEqual(reserva["estado"], "LIBERADA")
            self.assertIsNotNone(reserva["fecha_cierre"])

    def test_personal_sucursal_no_puede_cancelar_pedido(self):
        with self.assertRaises(PermisoDenegado):
            cancelar_pedido(self.pedido_id, "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path)

    def test_no_se_puede_cancelar_despues_de_la_salida(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        with self.assertRaises(TransicionPedidoInvalida):
            cancelar_pedido(self.pedido_id, "ADMINISTRADOR", 7, self.db_path)

    def test_no_se_puede_cancelar_un_pedido_entregado(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "EN_CAMINO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        registrar_fecha_entrega(self.entrega["id"], "2026-11-12T11:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "ENTREGADO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        with self.assertRaises(TransicionPedidoInvalida):
            cancelar_pedido(self.pedido_id, "ADMINISTRADOR", 7, self.db_path)

    def test_personal_de_sucursal_registra_incidencia_de_su_sucursal(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "PRODUCTO_FALTANTE",
            "El pedido llegó sin uno de los productos.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        self.assertEqual(incidencia["estado"], "ABIERTA")
        self.assertEqual(incidencia["categoria"], "PRODUCTO_FALTANTE")
        self.assertEqual(incidencia["pedido_id"], self.pedido_id)

    def test_personal_de_otra_sucursal_no_puede_reportar(self):
        with connect_database(self.db_path) as db:
            otra = db.execute(
                "SELECT id FROM sucursales WHERE codigo='DEMO-SUR'"
            ).fetchone()["id"]
        with self.assertRaises(PermisoDenegado):
            registrar_incidencia(
                self.pedido_id, "RETRASO", "El pedido presenta retraso.",
                "PERSONAL_SUCURSAL", otra, self.db_path
            )

    def test_repartidor_solo_reporta_su_entrega(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "RETRASO", "El tráfico retrasó la entrega.",
            "REPARTIDOR", self.repartidor["id"], self.db_path
        )
        self.assertEqual(incidencia["reportado_por_rol"], "REPARTIDOR")

    def test_repartidor_no_puede_reportar_pedido_ajeno(self):
        otro = registrar_repartidor("REP-S3-003", "Repartidor ajeno", self.db_path)
        with self.assertRaises(PermisoDenegado):
            registrar_incidencia(
                self.pedido_id, "RETRASO", "El tráfico retrasó la entrega.",
                "REPARTIDOR", otro["id"], self.db_path
            )

    def test_asesor_puede_consultar_y_resolver_incidencia(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "OTRO", "El cliente solicita ayuda con el pedido.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        en_revision = actualizar_estado_incidencia(
            incidencia["id"], "EN_REVISION", "ASESOR", 21, db_path=self.db_path
        )
        self.assertEqual(en_revision["estado"], "EN_REVISION")
        resuelta = actualizar_estado_incidencia(
            incidencia["id"], "RESUELTA", "ASESOR", 21,
            "Se contactó al cliente y se brindó una solución.", self.db_path
        )
        self.assertEqual(resuelta["estado"], "RESUELTA")
        self.assertIsNotNone(resuelta["fecha_resolucion"])

    def test_solo_asesor_o_admin_puede_atender_incidencias(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "RETRASO", "El pedido presenta retraso.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        with self.assertRaises(PermisoDenegado):
            actualizar_estado_incidencia(
                incidencia["id"], "EN_REVISION", "REPARTIDOR",
                self.repartidor["id"], db_path=self.db_path
            )

    def test_no_se_puede_resolver_sin_pasar_por_revision(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "OTRO", "Se requiere contactar al cliente.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        with self.assertRaises(TransicionIncidenciaInvalida):
            actualizar_estado_incidencia(
                incidencia["id"], "RESUELTA", "ASESOR", 21,
                "Problema resuelto correctamente.", self.db_path
            )

    def test_no_se_puede_resolver_sin_descripcion_de_solucion(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "OTRO", "Se requiere contactar al cliente.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        actualizar_estado_incidencia(
            incidencia["id"], "EN_REVISION", "ASESOR", 21, db_path=self.db_path
        )
        with self.assertRaises(ErrorSoportePedido):
            actualizar_estado_incidencia(
                incidencia["id"], "RESUELTA", "ASESOR", 21, db_path=self.db_path
            )

    def test_consulta_de_incidencias_respeta_el_rol(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "RETRASO", "El pedido presenta retraso.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        resultados = listar_incidencias(
            "PERSONAL_SUCURSAL", self.sucursal_id, db_path=self.db_path
        )
        self.assertEqual([x["id"] for x in resultados], [incidencia["id"]])
        self.assertEqual(len(listar_incidencias("ASESOR", db_path=self.db_path)), 1)

    def test_repartidor_no_consulta_incidencias_de_otras_entregas(self):
        incidencia = registrar_incidencia(
            self.pedido_id, "RETRASO", "El pedido presenta retraso.",
            "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
        )
        otro = registrar_repartidor("REP-S3-004", "Otro repartidor", self.db_path)
        self.assertEqual(
            listar_incidencias("REPARTIDOR", otro["id"], db_path=self.db_path), []
        )
        self.assertEqual(
            len(listar_incidencias("REPARTIDOR", self.repartidor["id"], db_path=self.db_path)), 1
        )

    def test_categoria_y_descripcion_se_validan(self):
        with self.assertRaises(DatosIncidenciaInvalidos):
            registrar_incidencia(
                self.pedido_id, "CATEGORIA_DESCONOCIDA", "Descripción válida.",
                "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
            )
        with self.assertRaises(ErrorSoportePedido):
            registrar_incidencia(
                self.pedido_id, "OTRO", "abc",
                "PERSONAL_SUCURSAL", self.sucursal_id, self.db_path
            )

    def test_consultar_incidencia_inexistente(self):
        with self.assertRaises(IncidenciaNoEncontrada):
            obtener_incidencia(99999, "ASESOR", db_path=self.db_path)

    def test_historial_de_pedido_se_conserva(self):
        registrar_fecha_salida(self.entrega["id"], "2026-11-12T10:00:00Z", self.db_path)
        cambiar_estado_pedido(
            self.pedido_id, "EN_CAMINO", "REPARTIDOR",
            self.repartidor["id"], self.db_path
        )
        historial = obtener_historial_pedido(self.pedido_id, self.db_path)
        self.assertEqual(historial[-1]["estado_nuevo"], "EN_CAMINO")


if __name__ == "__main__":
    unittest.main()
