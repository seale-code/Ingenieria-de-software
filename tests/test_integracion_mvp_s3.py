"""S3-05 / #17: contratos entre catálogo, pedidos, reservas y entregas reales."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.entregas_s3 import (
    EntregaDuplicada, obtener_historial_pedido, registrar_entrega,
    registrar_fecha_entrega, registrar_fecha_salida,
)
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor
from src.database.database import connect_database, get_stock, initialize_database
from src.database.migrate_josue import migrar


class IntegracionMvpS3Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'mvp.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path)
        iniciar_modulo(self.path)
        self.client = create_app(self.path).test_client()

    def confirmar(self, cantidad=2, token=None):
        return self.client.post('/api/pedidos', json=dict(
            cliente='Cliente ficticio', latitud=-12.0464, longitud=-77.0428,
            items=[dict(producto_codigo='DEMO-A', cantidad=cantidad)],
            confirmacion_id=token or str(uuid4())))

    def cantidad_catalogo(self):
        response = self.client.get('/api/catalogo?buscar=demo+a&sucursal=DEMO-NORTE')
        self.assertEqual(response.status_code, 200)
        return response.json['productos'][0]['cantidad']

    def cerrar_reserva(self, estado):
        # Fixture del contrato de persistencia. No sustituye el servicio S3-04.
        with connect_database(self.path) as db:
            db.execute("UPDATE reservas_stock SET estado=?, fecha_cierre="
                       "strftime('%Y-%m-%dT%H:%M:%fZ','now')", (estado,))

    def test_reserva_confirmada_reduce_disponibilidad_del_catalogo(self):
        self.assertEqual(self.cantidad_catalogo(), 5)
        self.assertEqual(self.confirmar().status_code, 200)
        self.assertEqual(self.cantidad_catalogo(), 3)
        fisico = get_stock(self.path, branch='DEMO-NORTE')[0]['cantidad']
        self.assertEqual(fisico, 5, 'Reservar no consume inventario físico')

    def test_stock_por_sucursal_refleja_reservas(self):
        self.confirmar()
        response = self.client.get('/api/productos/DEMO-A/stock')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['stock'][0]['cantidad'], 3)

    def test_agotado_por_reservas_no_aparece_en_disponibles(self):
        self.assertEqual(self.confirmar(cantidad=5).status_code, 200)
        response = self.client.get('/api/catalogo?buscar=demo+a&solo_disponibles=true')
        self.assertEqual(response.json['productos'], [])
        self.assertEqual(self.cantidad_catalogo(), 0)

    def test_liberar_restablece_disponibilidad_sin_consumo(self):
        self.confirmar()
        self.cerrar_reserva('LIBERADA')
        self.assertEqual(self.cantidad_catalogo(), 5)

    def test_consumir_no_descuenta_dos_veces_en_catalogo(self):
        self.confirmar()
        self.cerrar_reserva('CONSUMIDA')
        self.assertEqual(self.cantidad_catalogo(), 3)
        self.assertEqual(get_stock(self.path, branch='DEMO-NORTE')[0]['cantidad'], 3)

    def test_reintento_no_duplica_pedido_reserva_ni_historial(self):
        token = str(uuid4())
        primero, segundo = self.confirmar(token=token), self.confirmar(token=token)
        self.assertEqual(primero.status_code, 200)
        self.assertEqual(segundo.status_code, 200)
        self.assertEqual(primero.json, segundo.json)
        with connect_database(self.path) as db:
            for tabla in ('pedidos', 'reservas_stock', 'historial_estados'):
                self.assertEqual(db.execute(f'SELECT count(*) FROM {tabla}').fetchone()[0], 1)
        self.assertEqual(self.cantidad_catalogo(), 3)

    def test_sin_stock_no_deja_pedido_ni_historial_parcial(self):
        self.assertEqual(self.confirmar(cantidad=6).status_code, 409)
        with connect_database(self.path) as db:
            for tabla in ('pedidos', 'detalles_pedido', 'reservas_stock', 'historial_estados'):
                self.assertEqual(db.execute(f'SELECT count(*) FROM {tabla}').fetchone()[0], 0)

    def test_confirmacion_invalida_no_escribe(self):
        self.assertEqual(self.confirmar(cantidad=0).status_code, 400)
        self.assertEqual(self.cantidad_catalogo(), 5)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM pedidos').fetchone()[0], 0)

    def test_pedido_web_se_relaciona_con_repartidor_e_historial(self):
        pedido = self.confirmar().json['pedido']['pedido_id']
        repartidor = registrar_repartidor('DEMO-REP', 'Repartidor ficticio', self.path)
        entrega = registrar_entrega(pedido, repartidor['id'], db_path=self.path)
        self.assertEqual(entrega['pedido_id'], pedido)
        self.assertEqual(entrega['estado_pedido'], 'ASIGNADO')
        self.assertEqual(obtener_historial_pedido(pedido, self.path)[0]['estado_nuevo'], 'ASIGNADO')
        with self.assertRaises(EntregaDuplicada):
            registrar_entrega(pedido, repartidor['id'], db_path=self.path)

    def test_fechas_no_equivalen_a_transiciones_de_estado(self):
        pedido = self.confirmar().json['pedido']['pedido_id']
        repartidor = registrar_repartidor('DEMO-REP', 'Repartidor ficticio', self.path)
        entrega = registrar_entrega(pedido, repartidor['id'], db_path=self.path)
        registrar_fecha_salida(entrega['id'], '2030-01-01T10:00:00Z', self.path)
        resultado = registrar_fecha_entrega(entrega['id'], '2030-01-01T11:00:00Z', self.path)
        # S3-03 registra fechas; la transición validada pertenece a #22.
        self.assertEqual(resultado['estado_entrega'], 'ASIGNADA')
        self.assertEqual(resultado['estado_pedido'], 'ASIGNADO')

    def test_historial_rechaza_modificacion_y_borrado(self):
        self.confirmar()
        for sql in ('UPDATE historial_estados SET estado_nuevo=\'ENTREGADO\'',
                    'DELETE FROM historial_estados'):
            with self.assertRaises(sqlite3.IntegrityError):
                with connect_database(self.path) as db:
                    db.execute(sql)

    def test_reservas_de_otro_producto_no_reducen_disponibilidad(self):
        self.confirmar()
        response = self.client.get('/api/catalogo?buscar=demo+b&sucursal=DEMO-SUR')
        self.assertEqual(response.json['productos'][0]['cantidad'], 3)
