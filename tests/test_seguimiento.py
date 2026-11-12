import tempfile
import unittest
from pathlib import Path
from src.backend.app import create_app
from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar

CODE = 'WEB-12345678-1234-4234-8234-123456789abc'

class SeguimientoTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / 'seguimiento.sqlite3'
        initialize_database(self.db, demo=True)
        migrar(self.db)
        with connect_database(self.db) as db:
            sucursal = db.execute('SELECT id FROM sucursales LIMIT 1').fetchone()[0]
            self.id = db.execute("INSERT INTO pedidos(codigo,sucursal_id,estado) VALUES (?,?,'ASIGNADO')", (CODE,sucursal)).lastrowid
        self.client = create_app(self.db).test_client()

    def consultar(self, codigo=CODE):
        return self.client.get('/api/seguimiento', headers={'X-Codigo-Pedido': codigo})

    def test_estado_historial_actualizacion_y_sin_datos_personales(self):
        with connect_database(self.db) as db:
            db.execute("UPDATE pedidos SET estado='EN_PREPARACION' WHERE id=?", (self.id,))
        response = self.consultar()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        pedido = response.json['pedido']
        self.assertEqual(pedido['estado'], 'EN_PREPARACION')
        self.assertEqual([h['estado'] for h in pedido['historial']], ['ASIGNADO','EN_PREPARACION'])
        self.assertNotIn('cliente', pedido)
        self.assertNotIn('latitud', pedido)
        self.assertNotIn('observacion', pedido['historial'][0])

    def test_codigo_inexistente(self):
        self.assertEqual(self.consultar(CODE[:-1]+'d').status_code, 404)

    def test_no_consulta_por_id_o_sql(self):
        for codigo in ('',str(self.id), "' OR 1=1 --"):
            self.assertEqual(self.consultar(codigo).status_code, 400)

    def test_estado_cancelado(self):
        with connect_database(self.db) as db:
            db.execute("UPDATE pedidos SET estado='CANCELADO' WHERE id=?", (self.id,))
        self.assertEqual(self.consultar().json['pedido']['etiqueta'], 'Cancelado')

    def test_base_no_disponible(self):
        client = create_app(self.db.parent / 'ausente.db').test_client()
        response = client.get('/api/seguimiento', headers={'X-Codigo-Pedido': CODE})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(str(self.db.parent), response.get_data(as_text=True))

    def test_pantalla_y_assets(self):
        self.assertEqual(self.client.get('/seguimiento').status_code, 200)
        self.assertEqual(self.client.get('/assets/seguimiento.js').status_code, 200)
        self.assertIn(b'/seguimiento', self.client.get('/').data)

    def test_sin_migracion_s3_responde_error_claro(self):
        path = self.db.parent / 'v2.db'
        initialize_database(path, demo=True)
        migrar(path, hasta=2)
        with connect_database(path) as db:
            sucursal = db.execute('SELECT id FROM sucursales LIMIT 1').fetchone()[0]
            db.execute("INSERT INTO pedidos(codigo,sucursal_id) VALUES (?,?)", (CODE,sucursal))
        response = create_app(path).test_client().get('/api/seguimiento', headers={'X-Codigo-Pedido': CODE})
        self.assertEqual(response.status_code, 503)

if __name__ == '__main__':
    unittest.main()
