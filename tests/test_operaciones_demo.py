"""Integración HTTP real del panel con SQLite v4 y los servicios de S2/S3."""
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor, actualizar_repartidor
from src.backend.reparto_integrado import avanzar_reparto
from src.backend.soporte_pedidos_s3 import PermisoDenegado
from src.database.database import initialize_database, connect_database, get_stock
from src.database.migrate_josue import migrar


class OperacionesDemoTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'panel.sqlite3'
        initialize_database(self.path, demo=True)
        migrar(self.path, hasta=4)
        iniciar_modulo(self.path)
        self.app = create_app(self.path, demo_key='clave-aleatoria-de-prueba-para-demo')
        self.app.testing = True
        self.client = self.app.test_client()
        self.driver = registrar_repartidor('REP-01','Repartidor ficticio',self.path)
        self.code = 'WEB-' + str(uuid4())
        response = self.client.post('/api/pedidos', json=dict(cliente='Cliente privado',latitud=-12.0,longitud=-77.05,
            confirmacion_id=self.code[4:],items=[dict(producto_codigo='DEMO-A',cantidad=2)]))
        self.assertEqual(response.status_code,200,response.json)
        self.pedido = response.json['pedido']['pedido_id']
        self.login()

    def login(self):
        response = self.client.post('/api/demo/sesion',json={'clave':self.app.config['DEMO_KEY']})
        self.assertEqual(response.status_code,200)
        self.csrf = response.json['csrf']
        return response

    def post(self,url,body):
        return self.client.post(url,json=body,headers={'X-CSRF-Token':self.csrf})

    def action(self,action,**fields):
        return self.post(f'/api/demo/pedidos/{self.pedido}/acciones',dict(accion=action,**fields))

    def prepare(self):
        for action in ('preparar','listo'):
            response = self.action(action)
            self.assertEqual(response.status_code,200,response.json)
        response = self.action('asignar',repartidor_id=self.driver['id'])
        self.assertEqual(response.status_code,200,response.json)

    def detail(self):
        response = self.client.get(f'/api/demo/pedidos/{self.pedido}')
        self.assertEqual(response.status_code,200,response.json)
        return response.json['pedido']

    def stock(self,effective=False):
        return next(r['cantidad'] for r in get_stock(self.path,effective=effective)
                    if r['producto_codigo']=='DEMO-A' and r['sucursal_codigo']=='DEMO-NORTE')

    def test_panel_deshabilitado_por_defecto_no_expone_datos(self):
        client = create_app(self.path,demo_key='').test_client()
        for url in ('/operaciones','/api/demo/pedidos',f'/api/demo/pedidos/{self.pedido}','/api/demo/sesion'):
            self.assertEqual(client.get(url).status_code,404)
        self.assertFalse(client.get('/api/contexto').json['operaciones_demo'])

    def test_sesion_requerida_y_clave_incorrecta(self):
        other = self.app.test_client()
        self.assertEqual(other.get('/api/demo/pedidos').status_code,401)
        self.assertEqual(other.post('/api/demo/sesion',json={'clave':'incorrecta'}).status_code,401)
        self.assertEqual(other.get(f'/api/demo/pedidos/{self.pedido}').status_code,401)
        self.assertIsNone(other.get('/api/demo/sesion').json['csrf'])

    def test_cookie_salida_y_rotacion_de_csrf(self):
        response = self.login()
        cookie = response.headers['Set-Cookie']
        self.assertIn('HttpOnly',cookie)
        self.assertIn('SameSite=Strict',cookie)
        previous = self.csrf
        self.login()
        self.assertNotEqual(previous,self.csrf)
        url = f'/api/demo/pedidos/{self.pedido}/acciones'
        self.assertEqual(self.client.post(url,json={'accion':'preparar'},headers={'X-CSRF-Token':previous}).status_code,403)
        self.assertEqual(self.client.delete('/api/demo/sesion',json={},headers={'X-CSRF-Token':self.csrf}).status_code,200)
        self.assertEqual(self.client.get('/api/demo/pedidos').status_code,401)

    def test_escrituras_exigen_csrf_json_y_origen(self):
        url = f'/api/demo/pedidos/{self.pedido}/acciones'
        self.assertEqual(self.client.post(url,json={'accion':'preparar'}).status_code,403)
        self.assertEqual(self.client.post(url,data='accion=preparar').status_code,400)
        self.assertEqual(self.client.post(url,json={'accion':'preparar'},headers={
            'X-CSRF-Token':self.csrf,'Origin':'https://otro.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/demo/sesion',json={'clave':self.app.config['DEMO_KEY']},headers={
            'Origin':'https://otro.example'}).status_code,403)
        self.assertEqual(self.detail()['estado'],'ASIGNADO')

    def test_token_csrf_unicode_se_rechaza_sin_error_interno(self):
        response = self.client.post(f'/api/demo/pedidos/{self.pedido}/acciones',
            json={'accion':'preparar'},headers={'X-CSRF-Token':'clave-inválida'})
        self.assertEqual(response.status_code,403)

    def test_base_incompatible_devuelve_error_sin_ruta_interna(self):
        self.app.config['DATABASE'] = self.path.with_name('no-existe-privado.sqlite3')
        response = self.client.get('/api/demo/pedidos')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('no-existe-privado',response.get_data(as_text=True))
        self.assertNotIn(str(self.path.parent),response.get_data(as_text=True))

    def test_no_admite_rol_ni_actor_elegidos_por_el_cliente(self):
        self.assertEqual(self.action('preparar',rol='ADMINISTRADOR',actor_id=1).status_code,400)
        self.assertEqual(self.detail()['estado'],'ASIGNADO')

    def test_recorrido_hasta_entregado_sin_doble_consumo(self):
        self.assertEqual(self.stock(),5)
        self.assertEqual(self.stock(True),3)
        self.prepare()
        for action, state, delivery in [('salir','EN_CAMINO','EN_CAMINO'),('entregar','ENTREGADO','ENTREGADA')]:
            first = self.action(action)
            self.assertEqual(first.status_code,200,first.json)
            before = self.detail()
            self.assertEqual(before['estado'],state)
            self.assertEqual(before['entrega']['estado'],delivery)
            self.assertEqual(self.action(action).status_code,200)
            self.assertEqual(self.detail(),before)
            self.assertEqual(self.stock(),3)
            self.assertEqual(self.stock(True),3)
            public = self.client.get('/api/seguimiento',headers={'X-Codigo-Pedido':self.code}).json['pedido']
            self.assertEqual(public['estado'],state)
            self.assertNotIn('Cliente privado',str(public))
        detail = self.detail()
        self.assertEqual([h['estado_nuevo'] for h in detail['historial']],
                         ['ASIGNADO','EN_PREPARACION','PREPARADO','EN_CAMINO','ENTREGADO'])
        self.assertLessEqual(detail['entrega']['fecha_salida'],detail['entrega']['fecha_entrega'])
        self.assertEqual(detail['items'][0]['estado_reserva'],'CONSUMIDA')

    def test_no_omite_preparacion_o_repartidor(self):
        self.assertEqual(self.action('listo').status_code,409)
        self.assertEqual(self.action('asignar',repartidor_id=self.driver['id']).status_code,409)
        self.assertEqual(self.action('salir').status_code,409)
        self.assertEqual(len(self.detail()['historial']),1)

    def test_salidas_concurrentes_consumen_una_sola_vez(self):
        self.prepare()
        def salir(_):
            return avanzar_reparto(self.pedido,'EN_CAMINO','REPARTIDOR',self.driver['id'],self.path)
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados = list(pool.map(salir,range(4)))
        self.assertEqual(sum(not r['reintento'] for r in resultados),1)
        self.assertEqual(self.stock(),3)
        self.assertEqual(len(self.detail()['historial']),4)

    def test_repartidor_incorrecto_o_inactivo_no_registra_salida(self):
        self.prepare()
        with self.assertRaises(PermisoDenegado):
            avanzar_reparto(self.pedido,'EN_CAMINO','REPARTIDOR',self.driver['id']+100,self.path)
        with self.assertRaises(PermisoDenegado):
            avanzar_reparto(self.pedido,'EN_CAMINO','ADMINISTRADOR',self.driver['id'],self.path)
        actualizar_repartidor(self.driver['id'],activo=False,db_path=self.path)
        self.assertEqual(self.action('salir').status_code,409)
        self.assertIsNone(self.detail()['entrega']['fecha_salida'])
        self.assertEqual(self.stock(),5)

    def test_error_de_salida_revierte_fecha_stock_estado_e_historial(self):
        self.prepare()
        before = self.detail()
        with connect_database(self.path) as db:
            db.executescript("""CREATE TRIGGER falla_reparto BEFORE UPDATE OF estado ON entregas
                WHEN NEW.estado='EN_CAMINO' BEGIN SELECT RAISE(ABORT,'fallo inyectado'); END;""")
        self.assertEqual(self.action('salir').status_code,503)
        self.assertEqual(self.detail(),before)
        self.assertEqual(self.stock(),5)
        with connect_database(self.path) as db:
            db.execute('DROP TRIGGER falla_reparto')
        self.assertEqual(self.action('salir').status_code,200)
        self.assertEqual(self.stock(),3)

    def test_error_de_recepcion_no_deja_fecha_ni_estado_parcial(self):
        self.prepare()
        self.assertEqual(self.action('salir').status_code,200)
        before = self.detail()
        with connect_database(self.path) as db:
            db.executescript("""CREATE TRIGGER falla_recepcion BEFORE UPDATE OF estado ON entregas
                WHEN NEW.estado='ENTREGADA' BEGIN SELECT RAISE(ABORT,'fallo inyectado'); END;""")
        self.assertEqual(self.action('entregar').status_code,503)
        self.assertEqual(self.detail(),before)
        self.assertEqual(self.stock(),3)

    def test_no_despacha_con_reserva_liberada(self):
        self.prepare()
        # Fixture deliberadamente incoherente: el flujo web no libera sin cancelar.
        with connect_database(self.path) as db:
            db.execute("UPDATE reservas_stock SET estado='LIBERADA',fecha_cierre=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE pedido_id=?",(self.pedido,))
        self.assertEqual(self.action('salir').status_code,409)
        self.assertIsNone(self.detail()['entrega']['fecha_salida'])

    def test_cancelacion_libera_sin_descontar_y_bloquea_avances(self):
        self.prepare()
        self.assertEqual(self.action('cancelar').status_code,200)
        detail = self.detail()
        self.assertEqual(detail['estado'],'CANCELADO')
        self.assertEqual(detail['entrega']['estado'],'FALLIDA')
        self.assertEqual(detail['items'][0]['estado_reserva'],'LIBERADA')
        self.assertEqual(self.stock(),5)
        self.assertEqual(self.stock(True),5)
        for action in ('preparar','salir','cancelar'):
            self.assertEqual(self.action(action).status_code,409)

    def test_no_cancela_despues_de_salida(self):
        self.prepare()
        self.action('salir')
        self.assertEqual(self.action('cancelar').status_code,409)
        self.assertEqual(self.detail()['estado'],'EN_CAMINO')

    def test_incidencia_resuelta_y_privacidad_del_seguimiento(self):
        response = self.post(f'/api/demo/pedidos/{self.pedido}/incidencias',{
            'categoria':'RETRASO','descripcion':'<img src=x onerror=alert(1)> detalle privado'})
        self.assertEqual(response.status_code,201,response.json)
        incident = response.json['incidencia']['id']
        url = f'/api/demo/incidencias/{incident}/atender'
        self.assertEqual(self.post(url,{'estado':'RESUELTA','resolucion':'Resuelto de prueba'}).status_code,409)
        self.assertEqual(self.post(url,{'estado':'EN_REVISION'}).status_code,200)
        self.assertEqual(self.post(url,{'estado':'RESUELTA','resolucion':'x'}).status_code,409)
        self.assertEqual(self.post(url,{'estado':'RESUELTA','resolucion':'Solución ficticia documentada.'}).status_code,200)
        self.assertEqual(self.detail()['incidencias'][0]['estado'],'RESUELTA')
        public = self.client.get('/api/seguimiento',headers={'X-Codigo-Pedido':self.code})
        self.assertNotIn('detalle privado',public.get_data(as_text=True))
        self.assertNotIn('Cliente privado',public.get_data(as_text=True))
        self.assertEqual(public.headers['Cache-Control'],'no-store')

    def test_bandeja_resumen_y_lectura_no_modifican_datos(self):
        before = self.detail()
        for _ in range(3):
            response = self.client.get('/api/demo/pedidos')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['resumen']['activos'],1)
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertEqual(response.headers['X-Frame-Options'],'DENY')
        self.assertEqual(self.detail(),before)

    def test_carga_de_demo_aislada(self):
        from scripts.demo_web import preparar_demo
        path = self.path.with_name('solo-demo.sqlite3')
        preparar_demo(path)
        with connect_database(path) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT count(*) FROM pedidos').fetchone()[0],3)
            self.assertEqual(db.execute('SELECT count(*) FROM productos').fetchone()[0],6)
        self.assertEqual(self.stock(),5)


if __name__ == '__main__':
    unittest.main()
