"""S2-02 / #20: contrato HTTP de confirmación y reintentos seguros."""
import concurrent.futures
import tempfile
import threading
import unittest
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


def datos(cantidad=2):
    return dict(cliente='Cliente ficticio', latitud=-12, longitud=-77.05,
                items=[dict(producto_codigo='DEMO-A', cantidad=cantidad)], confirmacion_id=str(uuid4()))


class PedidosWebTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'web.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path, hasta=2)
        iniciar_modulo(self.path)
        self.app = create_app(self.path)
        self.client = self.app.test_client()

    def total(self, tabla='pedidos'):
        self.assertIn(tabla, ('pedidos', 'reservas_stock'))
        with connect_database(self.path) as db:
            return db.execute('SELECT count(*) FROM ' + tabla).fetchone()[0]

    def test_formulario_y_opciones_no_escriben(self):
        self.assertEqual(self.client.get('/pedido').status_code, 200)
        self.assertEqual(self.client.get('/assets/pedido.js').status_code, 200)
        response = self.client.get('/api/pedidos/opciones')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['productos']), 3)
        self.assertEqual(len(response.json['puntos']), 2)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.total(), 0)

    def test_confirmar_persiste_reserva_y_sucursal(self):
        response = self.client.post('/api/pedidos', json=datos())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['pedido']['sucursal_codigo'], 'DEMO-NORTE')
        self.assertEqual(self.total(), 1)
        self.assertEqual(self.total('reservas_stock'), 1)

    def test_no_acepta_solicitud_sin_clave_ni_json(self):
        for payload in [None, [], {}, {'confirmacion_id': 'incorrecto'}]:
            response = self.client.post('/api/pedidos', json=payload)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post('/api/pedidos', data='{}', content_type='text/plain').status_code, 400)
        self.assertEqual(self.total(), 0)

    def test_cantidades_y_productos_invalidos(self):
        for cantidad in (0, -1, True, 1.5, '2', 10001):
            with self.subTest(cantidad=cantidad):
                self.assertEqual(self.client.post('/api/pedidos', json=datos(cantidad)).status_code, 400)
        payload = datos()
        payload['items'][0]['producto_codigo'] = 'NO-EXISTE'
        self.assertEqual(self.client.post('/api/pedidos', json=payload).status_code, 400)
        self.assertEqual(self.total(), 0)

    def test_sin_stock_es_error_claro_sin_insertar(self):
        response = self.client.post('/api/pedidos', json=datos(6))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['codigo'], 'SIN_STOCK_DISPONIBLE')
        self.assertEqual(self.total(), 0)

    def test_repetir_confirmacion_recupera_mismo_pedido(self):
        payload = datos()
        first = self.client.post('/api/pedidos', json=payload)
        second = self.client.post('/api/pedidos', json=payload)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json, second.json)
        self.assertEqual(self.total(), 1)
        self.assertEqual(self.total('reservas_stock'), 1)

    def test_clave_reutilizada_con_datos_distintos_se_rechaza(self):
        payload = datos()
        self.client.post('/api/pedidos', json=payload)
        payload['items'][0]['cantidad'] = 3
        response = self.client.post('/api/pedidos', json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['codigo'], 'CONFIRMACION_REUTILIZADA')
        self.assertEqual(self.total(), 1)

    def test_misma_clave_concurrente_crea_un_solo_pedido(self):
        payload = datos()
        barrier = threading.Barrier(2)
        def post():
            barrier.wait(timeout=5)
            return self.app.test_client().post('/api/pedidos', json=payload)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(post) for _ in range(2)]
            results = [f.result(timeout=10) for f in futures]
        self.assertEqual([r.status_code for r in results], [200, 200])
        self.assertEqual(results[0].json, results[1].json)
        self.assertEqual(self.total(), 1)
        self.assertEqual(self.total('reservas_stock'), 1)

    def test_dos_confirmaciones_no_sobrevenden(self):
        barrier = threading.Barrier(2)
        def post():
            barrier.wait(timeout=5)
            return self.app.test_client().post('/api/pedidos', json=datos(3)).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(post) for _ in range(2)]
            results = [f.result(timeout=10) for f in futures]
        self.assertEqual(sorted(results), [200, 409])
        self.assertEqual(self.total(), 1)

    def test_base_v1_requiere_esquema_oficial(self):
        path = self.path.parent / 'v1.sqlite3'
        initialize_database(path, demo=True)
        iniciar_modulo(path)
        response = create_app(path).test_client().post('/api/pedidos', json=datos())
        self.assertEqual(response.status_code, 503)
        with connect_database(path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM s2_pedidos').fetchone()[0], 0)

    def test_base_ausente_no_expone_ruta_ni_crea_archivo(self):
        path = self.path.parent / 'no-existe.sqlite3'
        response = create_app(path).test_client().post('/api/pedidos', json=datos())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(str(path), response.get_data(as_text=True))
        self.assertFalse(path.exists())

    def test_rollback_permite_reintento_con_la_misma_clave(self):
        with connect_database(self.path) as db:
            db.execute("CREATE TRIGGER fallo_web BEFORE INSERT ON reservas_stock BEGIN SELECT RAISE(ABORT,'fallo de prueba'); END")
        payload = datos()
        self.assertEqual(self.client.post('/api/pedidos', json=payload).status_code, 503)
        self.assertEqual(self.total(), 0)
        with connect_database(self.path) as db:
            db.execute('DROP TRIGGER fallo_web')
        self.assertEqual(self.client.post('/api/pedidos', json=payload).status_code, 200)
        self.assertEqual(self.total(), 1)
