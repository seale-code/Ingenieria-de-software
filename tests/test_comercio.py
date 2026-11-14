"""Cotización, precios persistidos y compatibilidad sobre bases reales v4/v5."""
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo,registrar_pedido
from src.database.catalogo_comercial import PRODUCTOS,cargar_catalogo
from src.database.database import connect_database,initialize_database
from src.database.migrate_josue import migrar


class ComercioTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'tienda.sqlite3';preparar_tienda(self.path)
        self.app=create_app(self.path,operations_key='clave-para-pruebas-de-operaciones')
        self.app.testing=True;self.client=self.app.test_client()

    def quote(self,items=None):
        response=self.client.post('/api/pedidos/cotizacion',json={'items':items or [{'producto_codigo':'023735','cantidad':1}]})
        self.assertEqual(response.status_code,200,response.json)
        return response.json['cotizacion']

    def payload(self,quote=None):
        q=quote or self.quote()
        return dict(cliente='Cliente de prueba',confirmacion_id=str(uuid4()),
            items=[dict(producto_codigo=p['producto_codigo'],cantidad=p['cantidad']) for p in q['items']],
            comercio=dict(cotizacion_id=q['cotizacion_id'],telefono='987654321',direccion='Calle de prueba 123',distrito='MIRAFLORES'))

    def post(self,data):
        return self.client.post('/api/pedidos',json=data)

    def count(self):
        with connect_database(self.path,read_only=True) as db:
            return db.execute('SELECT count(*) FROM pedidos').fetchone()[0]

    def test_catalogo_con_precios_fotos_y_presentaciones(self):
        data=self.client.get('/api/catalogo').json
        self.assertEqual(data['total'],16)
        for p in data['productos']:
            self.assertGreater(p['precio_centimos'],0)
            self.assertGreaterEqual(p['precio_lista_centimos'],p['precio_centimos'])
            self.assertTrue(p['imagen'].startswith('/assets/imagenes/productos/'))
            self.assertEqual(self.client.get(p['imagen']).status_code,200)
            self.assertNotIn('demo',p['producto'].lower())
        self.assertEqual(self.client.get('/assets/imagenes/inkafarma.svg').status_code,200)

    def test_v5_no_publica_productos_ni_filtros_sin_catalogo_comercial(self):
        with connect_database(self.path) as db:
            categoria=db.execute("INSERT INTO categorias(codigo,nombre) VALUES('LEGACY','Categoría anterior')").lastrowid
            producto=db.execute("INSERT INTO productos(codigo,nombre,categoria_id) VALUES('ANTERIOR','Producto anterior',?)",(categoria,)).lastrowid
            sucursal=db.execute("INSERT INTO sucursales(codigo,nombre,latitud,longitud) VALUES('ANTERIOR','Sucursal anterior',0,0)").lastrowid
            db.execute('INSERT INTO inventario VALUES(?,?,5)',(producto,sucursal))
        self.assertEqual(self.client.get('/api/catalogo').json['total'],16)
        self.assertEqual(self.client.get('/api/catalogo?buscar=anterior').json['total'],0)
        self.assertEqual(len(self.client.get('/api/pedidos/opciones').json['productos']),16)
        filters=self.client.get('/api/filtros').json
        self.assertNotIn('LEGACY',[p['codigo'] for p in filters['categorias']])
        self.assertNotIn('ANTERIOR',[p['codigo'] for p in filters['sucursales']])

    def test_cotizacion_exacta_y_lineas_agrupadas(self):
        q=self.quote([{'producto_codigo':'023735','cantidad':1},{'producto_codigo':'023735','cantidad':1}])
        self.assertEqual(len(q['items']),1)
        self.assertEqual(q['subtotal_centimos'],15380)
        self.assertEqual(q['envio_centimos'],0)
        self.assertEqual(q['total_centimos'],15380)
        self.assertEqual(self.count(),0)

    def test_limite_envio_gratis_en_centimos(self):
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=14900,precio_lista_centimos=14900 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        self.assertEqual(self.quote()['envio_centimos'],0)
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=14899 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        q=self.quote()
        self.assertEqual(q['envio_centimos'],690)
        self.assertEqual(q['total_centimos'],15589)

    def test_cotizar_no_reserva_ni_crea_historial(self):
        for _ in range(3):self.quote()
        with connect_database(self.path) as db:
            for table in ['pedidos','reservas_stock','precios_pedido','historial_estados']:
                self.assertEqual(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0],0)

    def test_cantidades_y_productos_invalidos(self):
        for items in [[],[{'producto_codigo':'NO-EXISTE','cantidad':1}],
                [{'producto_codigo':'036723','cantidad':3}],
                [{'producto_codigo':'023735','cantidad':True}],
                [{'producto_codigo':'023735','cantidad':1.5}],
                [{'producto_codigo':'023735','cantidad':0}],
                [{'producto_codigo':'036723','cantidad':2},{'producto_codigo':'036723','cantidad':1}]]:
            with self.subTest(items=items):
                self.assertEqual(self.client.post('/api/pedidos/cotizacion',json={'items':items}).status_code,400)
        self.assertEqual(self.count(),0)

    def test_confirmacion_incluye_importes_y_pago_al_recibir(self):
        response=self.post(self.payload());self.assertEqual(response.status_code,200,response.json)
        data=response.json['pedido'];commerce=data['comercio']
        self.assertEqual(commerce['total_centimos'],8380)
        self.assertEqual(commerce['metodo_pago'],'AL_RECIBIR')
        self.assertEqual(data['sucursal_codigo'],'MIRAFLORES')
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM precios_pedido').fetchone()[0],1)
            self.assertEqual(db.execute("SELECT cantidad FROM inventario i JOIN productos p ON p.id=i.producto_id JOIN sucursales s ON s.id=i.sucursal_id WHERE p.codigo='023735' AND s.codigo='MIRAFLORES'").fetchone()[0],18)

    def test_no_permite_omitir_datos_comerciales_en_nuevos_pedidos(self):
        data=self.payload();data.pop('comercio')
        self.assertEqual(self.post(data).status_code,400)
        self.assertEqual(self.count(),0)

    def test_cliente_no_decide_precio_ni_coordenadas_del_distrito(self):
        data=self.payload();data.update(latitud=0,longitud=0,total_centimos=1)
        data['items'][0]['precio_centimos']=1
        response=self.post(data);self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(response.json['pedido']['comercio']['total_centimos'],8380)
        self.assertEqual(response.json['pedido']['sucursal_codigo'],'MIRAFLORES')
        data=self.payload();data['comercio']['total_centimos']=1
        self.assertEqual(self.post(data).status_code,400)

    def test_precio_actualizado_exige_otra_revision_sin_reserva(self):
        data=self.payload()
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=7700 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        response=self.post(data)
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json['codigo'],'PRECIO_ACTUALIZADO')
        self.assertEqual(self.count(),0)
        data['comercio']['cotizacion_id']=self.quote()['cotizacion_id']
        self.assertEqual(self.post(data).status_code,200)

    def test_reintento_conserva_importe_aunque_cambie_catalogo(self):
        data=self.payload();first=self.post(data)
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=7700 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        repeated=self.post(data)
        self.assertEqual(repeated.status_code,200,repeated.json)
        self.assertEqual(first.json,repeated.json)
        self.assertEqual(self.count(),1)

    def test_confirmacion_no_se_reutiliza_para_otra_direccion(self):
        data=self.payload();self.assertEqual(self.post(data).status_code,200)
        data['comercio']['direccion']='Otra dirección 456'
        response=self.post(data)
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json['codigo'],'CONFIRMACION_REUTILIZADA')
        self.assertEqual(self.count(),1)

    def test_validacion_de_contacto_y_distrito(self):
        for field,value in [('telefono','123'),('telefono',987654321),('direccion','x'),('direccion',None),('distrito','FUERA-COBERTURA'),('cotizacion_id','abc')]:
            data=self.payload();data['comercio'][field]=value
            self.assertEqual(self.post(data).status_code,400,(field,value))
        self.assertEqual(self.count(),0)

    def test_fallo_financiero_revierte_pedido_reservas_y_precios(self):
        with connect_database(self.path) as db:
            db.executescript("CREATE TRIGGER fallo_precio BEFORE INSERT ON precios_pedido BEGIN SELECT RAISE(ABORT,'fallo inyectado'); END;")
        response=self.post(self.payload())
        self.assertEqual(response.status_code,503)
        self.assertNotIn('fallo inyectado',str(response.json))
        with connect_database(self.path) as db:
            for table in ['pedidos','reservas_stock','pedidos_comerciales','precios_pedido','historial_estados']:
                self.assertEqual(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0],0)

    def test_confirmaciones_concurrentes_generan_un_solo_pedido(self):
        data=self.payload()
        def confirm(_):
            with self.app.test_client() as client:return client.post('/api/pedidos',json=data)
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(confirm,range(4)))
        self.assertTrue(all(r.status_code==200 for r in results))
        self.assertTrue(all(r.json==results[0].json for r in results))
        self.assertEqual(self.count(),1)

    def test_precios_confirmados_son_inmutables(self):
        self.assertEqual(self.post(self.payload()).status_code,200)
        with connect_database(self.path) as db:
            for statement in ['UPDATE precios_pedido SET precio_unitario_centimos=1','DELETE FROM precios_pedido',
                              'UPDATE pedidos_comerciales SET total_centimos=1','DELETE FROM pedidos_comerciales']:
                with self.assertRaises(sqlite3.IntegrityError):db.execute(statement)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_datos_de_entrega_solo_en_operaciones_autorizadas(self):
        data=self.payload();result=self.post(data).json['pedido'];pedido=result['pedido_id']
        public=self.client.get('/api/seguimiento',headers={'X-Codigo-Pedido':'WEB-'+data['confirmacion_id']})
        for private in ['987654321','Calle de prueba','Cliente de prueba','direccion','telefono']:
            self.assertNotIn(private,public.get_data(as_text=True))
        self.assertEqual(self.client.get(f'/api/demo/pedidos/{pedido}').status_code,401)
        self.client.post('/api/demo/sesion',json={'clave':self.app.config['DEMO_KEY']})
        detail=self.client.get(f'/api/demo/pedidos/{pedido}').json['pedido']
        self.assertEqual(detail['comercio']['entrega']['telefono'],'987654321')
        self.assertEqual(detail['items'][0]['imagen'],'/assets/imagenes/productos/023735.webp')

    def test_reiniciar_no_restaura_stock_ni_precio(self):
        self.assertEqual(self.post(self.payload()).status_code,200)
        with connect_database(self.path) as db:
            db.execute("UPDATE catalogo_comercial SET precio_centimos=7700 WHERE producto_id=(SELECT id FROM productos WHERE codigo='023735')")
        preparar_tienda(self.path)
        self.assertEqual(self.count(),1)
        self.assertEqual(self.quote()['subtotal_centimos'],7700)
        with connect_database(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM reservas_stock').fetchone()[0],1)

    def test_migracion_preserva_pedidos_anteriores_y_su_seguimiento(self):
        path=self.path.with_name('anterior.sqlite3');initialize_database(path,demo=True);migrar(path,hasta=4);iniciar_modulo(path)
        pedido=registrar_pedido(dict(cliente='Anterior',latitud=-12,longitud=-77.05,items=[dict(producto_codigo='DEMO-A',cantidad=2)]),path)
        with connect_database(path) as db:code=db.execute('SELECT codigo FROM pedidos WHERE id=?',(pedido['pedido_id'],)).fetchone()[0]
        migrar(path,hasta=5)
        client=create_app(path).test_client();response=client.get('/api/seguimiento',headers={'X-Codigo-Pedido':code})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['pedido']['estado'],'ASIGNADO')
        with connect_database(path) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM reservas_stock WHERE estado='ACTIVA'").fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM pedidos_comerciales').fetchone()[0],0)

    def test_paginas_no_contienen_mensajes_de_prototipo(self):
        for url in ['/','/pedido','/seguimiento','/operaciones','/ayuda','/privacidad']:
            response=self.client.get(url);self.assertEqual(response.status_code,200)
            html=response.get_data(as_text=True).lower()
            for word in ['académic','fictici','demostración','prototipo','simula los roles']:
                self.assertNotIn(word,html,(url,word))

    def test_catalogo_fuentes_y_recursos_incluidos(self):
        data=json.loads(PRODUCTOS.read_text())
        for p in data:
            self.assertTrue(p['fuente'].startswith('https://inkafarma.pe/producto/'))
            self.assertEqual(p['consultado'],'2026-11-13')
            self.assertTrue((Path('src/frontend')/p['imagen'].removeprefix('/assets/')).is_file())


if __name__=='__main__':unittest.main()
