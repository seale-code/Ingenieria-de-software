"""S3-05: integración de confirmación y preparación con el seguimiento de Willy."""
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo, registrar_pedido
from src.backend.preparacion_pedidos import (
    completar_preparacion_pedido, iniciar_preparacion_pedido,
    TransicionPreparacionInvalida,
)
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class IntegracionSeguimientoS3Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'integrado.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path)
        iniciar_modulo(self.path)
        self.client = create_app(self.path).test_client()
        self.token = str(uuid4())
        self.code = 'WEB-' + self.token
        self.solicitud = dict(cliente='Cliente confidencial de prueba', latitud=-12.0464,
            longitud=-77.0428, items=[dict(producto_codigo='DEMO-A', cantidad=2)],
            confirmacion_id=self.token)
        response = self.client.post('/api/pedidos', json=self.solicitud)
        self.assertEqual(response.status_code, 200)
        self.pedido = response.json['pedido']['pedido_id']

    def consulta(self, code=None):
        return self.client.get('/api/seguimiento', headers={'X-Codigo-Pedido': code or self.code})

    def test_estado_e_historial_siguen_preparacion_real_sin_sql_de_avance(self):
        self.assertEqual(self.consulta().json['pedido']['estado'], 'ASIGNADO')
        iniciar_preparacion_pedido(self.pedido, self.path)
        self.assertEqual(self.consulta().json['pedido']['estado'], 'EN_PREPARACION')
        completar_preparacion_pedido(self.pedido, self.path)
        pedido = self.consulta().json['pedido']
        self.assertEqual(pedido['estado'], 'PREPARADO')
        self.assertEqual([r['estado'] for r in pedido['historial']],
                         ['ASIGNADO', 'EN_PREPARACION', 'PREPARADO'])

    def test_reintentar_confirmacion_y_consultar_no_duplica_escrituras(self):
        self.assertEqual(self.client.post('/api/pedidos', json=self.solicitud).status_code, 200)
        for _ in range(3):
            self.assertEqual(self.consulta().json['pedido']['numero'], self.pedido)
        with connect_database(self.path) as db:
            for tabla in ('pedidos', 'detalles_pedido', 'reservas_stock', 'historial_estados'):
                self.assertEqual(db.execute(f'SELECT count(*) FROM {tabla}').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT cantidad FROM inventario WHERE producto_id=1 AND sucursal_id=1').fetchone()[0], 5)

    def test_respuesta_publica_no_expone_metadata_ni_observaciones(self):
        with connect_database(self.path) as db:
            db.execute("INSERT INTO historial_estados(pedido_id,estado_nuevo,observacion) "
                       "VALUES (?,'ASIGNADO','Nota interna privada')", (self.pedido,))
        response = self.consulta()
        pedido = response.json['pedido']
        self.assertEqual(set(pedido), {'numero', 'estado', 'etiqueta', 'mensaje', 'sucursal', 'historial'})
        for row in pedido['historial']:
            self.assertEqual(set(row), {'estado', 'etiqueta', 'fecha'})
        for private in (self.solicitud['cliente'], 'Nota interna privada', self.code, '-77.0428'):
            self.assertNotIn(private, response.get_data(as_text=True))

    def test_codigo_en_query_no_reemplaza_cabecera_y_error_no_se_cachea(self):
        response = self.client.get('/api/seguimiento', query_string={'codigo': self.code})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.consulta().status_code, 200)

    def test_salto_preparacion_rechazado_no_inventa_evento_en_seguimiento(self):
        with self.assertRaises(TransicionPreparacionInvalida):
            completar_preparacion_pedido(self.pedido, self.path)
        data = self.consulta().json['pedido']
        self.assertEqual(data['estado'], 'ASIGNADO')
        self.assertEqual([r['estado'] for r in data['historial']], ['ASIGNADO'])

    def test_pedido_del_cli_tambien_admite_seguimiento(self):
        result = registrar_pedido({**self.solicitud, 'items': [dict(producto_codigo='DEMO-B', cantidad=1)]}, self.path)
        with connect_database(self.path) as db:
            code = db.execute('SELECT codigo FROM pedidos WHERE id=?', (result['pedido_id'],)).fetchone()[0]
        self.assertTrue(code.startswith('S2-'))
        self.assertEqual(self.consulta(code).json['pedido']['numero'], result['pedido_id'])
