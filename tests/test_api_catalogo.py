"""S1-11: contrato HTTP con SQLite temporal real, sin simular las consultas."""
import tempfile
import unittest
from pathlib import Path

from src.backend.app import create_app
from src.database.database import connect_database, initialize_database
from src.database.migrate_josue import migrar


class CatalogoApiTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'catalogo.sqlite3'
        initialize_database(self.path, demo=True)
        self.app = create_app(self.path)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def catalogo(self, **query):
        response = self.client.get('/api/catalogo', query_string=query)
        self.assertEqual(response.status_code, 200)
        return response.get_json()['productos']

    def codes(self, **query):
        return [p['producto_codigo'] for p in self.catalogo(**query)]

    def test_pantalla_y_recursos(self):
        for path in ['/', '/assets/styles.css', '/assets/catalogo.js']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get('/assets/../../data/inkafarma.sqlite3').status_code, 404)

    def test_catalogo_sin_duplicados(self):
        self.assertEqual(self.codes(), ['DEMO-A', 'DEMO-B', 'DEMO-C'])

    def test_busqueda_exacta_parcial_y_vacia(self):
        self.assertEqual(self.codes(buscar='Producto demo A'), ['DEMO-A'])
        self.assertEqual(self.codes(buscar='  DEMO b '), ['DEMO-B'])
        self.assertEqual(self.codes(buscar='xyz123'), [])

    def test_categoria_y_limpiar(self):
        self.assertEqual(self.codes(categoria='DEMO-X'), ['DEMO-A', 'DEMO-C'])
        self.assertEqual(len(self.codes(categoria='')), 3)

    def test_disponibles_por_sucursal(self):
        self.assertEqual(self.codes(sucursal='DEMO-NORTE', solo_disponibles='true'), ['DEMO-A'])
        self.assertEqual(self.codes(sucursal='DEMO-SUR', solo_disponibles='true'), ['DEMO-B'])
        self.assertEqual(len(self.codes(sucursal='DEMO-NORTE')), 3)

    def test_combinacion_de_todos_los_filtros(self):
        query = dict(buscar='demo b', categoria='DEMO-Y', sucursal='DEMO-SUR', solo_disponibles='true')
        self.assertEqual(self.codes(**query), ['DEMO-B'])
        query['categoria'] = 'DEMO-X'
        self.assertEqual(self.codes(**query), [])

    def test_stock_y_cero(self):
        data = self.client.get('/api/productos/DEMO-A/stock').get_json()['stock']
        self.assertEqual([(r['sucursal_codigo'], r['cantidad']) for r in data], [('DEMO-NORTE', 5), ('DEMO-SUR', 0)])
        self.assertEqual(self.catalogo(buscar='demo c')[0]['cantidad'], 0)
        self.assertEqual(self.codes(buscar='demo c', solo_disponibles='true'), [])

    def test_categoria_vacia_y_producto_sin_inventario(self):
        with connect_database(self.path) as db:
            db.execute("INSERT INTO categorias(codigo,nombre) VALUES ('VACIA','Vacía')")
            db.execute("INSERT INTO productos(codigo,nombre,categoria_id) SELECT 'SIN-REGISTRO','Sin inventario',id FROM categorias WHERE codigo='DEMO-X'")
        self.assertIn('VACIA', [c['codigo'] for c in self.client.get('/api/filtros').get_json()['categorias']])
        self.assertEqual(self.codes(categoria='VACIA'), [])
        producto = self.catalogo(buscar='Sin inventario', categoria='DEMO-X')[0]
        self.assertIsNone(producto['cantidad'])
        self.assertEqual(self.client.get('/api/productos/SIN-REGISTRO/stock').get_json()['stock'], [])
        self.assertEqual(self.codes(buscar='Sin inventario', solo_disponibles='true'), [])

    def test_unicode_y_sql_literal(self):
        with connect_database(self.path) as db:
            db.execute("UPDATE productos SET nombre='Ácido de prueba' WHERE codigo='DEMO-A'")
        self.assertEqual(self.codes(buscar='ÁCIDO'), ['DEMO-A'])
        for value in ["' OR 1=1 --", '%', '_']:
            self.assertEqual(self.codes(buscar=value), [])
        self.assertEqual(len(self.codes()), 3)

    def test_stock_actualizado_no_cacheado(self):
        self.assertEqual(self.catalogo(buscar='demo a')[0]['cantidad'], 5)
        with connect_database(self.path) as db:
            db.execute("UPDATE inventario SET cantidad=2 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")
        response = self.client.get('/api/catalogo?buscar=demo+a')
        self.assertEqual(response.get_json()['productos'][0]['cantidad'], 2)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_errores_de_peticion(self):
        self.assertEqual(self.client.get('/api/catalogo?solo_disponibles=quizas').status_code, 400)
        self.assertEqual(self.client.get('/api/productos/NO-EXISTE/stock').status_code, 404)
        self.assertEqual(self.codes(sucursal='NO-EXISTE'), [])

    def test_base_ausente_no_se_crea_ni_filtra_ruta(self):
        missing = self.path.parent / 'ausente.sqlite3'
        client = create_app(missing).test_client()
        for url in ['/api/filtros', '/api/catalogo', '/api/productos/DEMO-A/stock']:
            response = client.get(url)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(str(missing), response.get_data(as_text=True))
        self.assertFalse(missing.exists())

    def test_base_invalida(self):
        self.path.write_text('base inválida')
        self.assertEqual(self.client.get('/api/catalogo').status_code, 503)

    def test_base_vacia(self):
        path = self.path.parent / 'vacia.sqlite3'
        initialize_database(path)
        client = create_app(path).test_client()
        self.assertEqual(client.get('/api/catalogo').get_json()['productos'], [])
        self.assertEqual(client.get('/api/filtros').get_json(), dict(categorias=[], sucursales=[]))

    def test_compatible_con_migraciones_de_josue(self):
        migrar(self.path)
        self.assertEqual(self.codes(), ['DEMO-A', 'DEMO-B', 'DEMO-C'])


if __name__ == '__main__':
    unittest.main()
