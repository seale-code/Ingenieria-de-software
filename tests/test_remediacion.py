"""Verificación del acceso, compra y transporte en la fábrica usada por la tienda."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import secrets
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.seguridad import emitir_codigo, guardar_usuario
from src.backend.logistica import procesar_vencimientos
from src.database.database import connect_database


class SeguridadTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'tienda.db'
        preparar_tienda(self.path)
        self.app=create_app(self.path)
        self.c=self.app.test_client()
        self.clave=secrets.token_urlsafe(24)
        for usuario,sede in [('central',None),('mira','MIRAFLORES'),('sur','SURCO')]:
            guardar_usuario(self.path,usuario,self.clave,sede)

    def login(self,c,usuario):
        return c.post('/api/demo/sesion',json=dict(usuario=usuario,clave=self.clave))

    def datos(self):
        items=[dict(producto_codigo='023735',cantidad=1)]
        q=self.c.post('/api/pedidos/cotizacion',json=dict(items=items)).json['cotizacion']
        return dict(items=items,cliente='Prueba',confirmacion_id=str(uuid4()),comercio=dict(
            telefono='987654321',direccion='Dirección de prueba',distrito='MIRAFLORES',cotizacion_id=q['cotizacion_id']))

    def codigo(self,d):
        r=self.c.post('/api/pedidos/verificacion', json=dict(telefono=d['comercio']['telefono'],confirmacion_id=d['confirmacion_id']))
        self.assertEqual(r.status_code,202)
        with self.app.app_context():
            _,d['codigo_celular']=emitir_codigo(d['confirmacion_id'])
        self.assertNotIn(d['codigo_celular'],r.get_data(as_text=True))

    def test_sucursal_central_revocacion_auditoria(self):
        d=self.datos();self.codigo(d)
        pedido=self.c.post('/api/pedidos',json=d).json['pedido']['pedido_id']
        url=f'/api/demo/pedidos/{pedido}'
        for usuario,esperado in [('mira',200),('sur',403),('central',200)]:
            c=self.app.test_client()
            login=self.login(c,usuario)
            self.assertEqual(login.status_code,200)
            self.assertEqual(c.get(url).status_code,esperado)
            lista=c.get('/api/demo/pedidos').json['pedidos']
            self.assertEqual(bool(lista),esperado==200)
            stock=c.get('/api/demo/inventario').json['existencias']
            sedes={r['sucursal_codigo'] for r in stock}
            self.assertEqual(len(sedes),3 if usuario=='central' else 1)
            cab={'X-CSRF-Token':login.json['csrf']}
            dmov=dict(producto_codigo='023735',sucursal_codigo='MIRAFLORES',tipo='ENTRADA',cantidad=1,
                      motivo='Control de recepción',solicitud_id=str(uuid4()))
            self.assertEqual(c.post('/api/demo/inventario/movimientos',json=dmov,headers=cab).status_code,esperado)
            self.assertEqual(c.post('/api/demo/inventario/movimientos',json=dmov).status_code,403)
        guardar_usuario(self.path,'central',secrets.token_urlsafe(24))
        self.assertEqual(c.get(url).status_code,401)
        with connect_database(self.path) as db:
            self.assertEqual([tuple(r) for r in db.execute('SELECT usuario,estado FROM auditoria_operaciones ORDER BY id')],
                             [('mira',200),('sur',403),('central',200)])

    def test_cupo_atomico_y_reintento(self):
        datos=[self.datos() for _ in range(3)]
        for d in datos:self.codigo(d)
        with ThreadPoolExecutor(max_workers=3) as pool:
            estados=list(pool.map(lambda d:self.app.test_client().post('/api/pedidos',json=d).status_code,datos))
        self.assertEqual(sorted(estados),[200,200,400])
        self.assertEqual(self.c.post('/api/pedidos',json=datos[estados.index(200)]).status_code,200)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reservas_stock').fetchone()[0],2)

    def test_limite_absoluto_libera_reserva(self):
        from datetime import datetime,timedelta,timezone
        d=self.datos();self.codigo(d);self.assertEqual(self.c.post('/api/pedidos',json=d).status_code,200)
        procesar_vencimientos(self.path,ahora=datetime.now(timezone.utc)+timedelta(minutes=46))
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT estado FROM pedidos').fetchone()[0],'CANCELADO')
            self.assertEqual(db.execute('SELECT estado FROM reservas_stock').fetchone()[0],'LIBERADA')

    def test_codigo_vinculado_y_vencimiento(self):
        d=self.datos()
        self.assertEqual(self.c.post('/api/pedidos',json=d).status_code,403)
        self.codigo(d)
        for alterado in [dict(d,confirmacion_id=str(uuid4())),dict(d,comercio=dict(d['comercio'],telefono='912345678'))]:
            self.assertEqual(self.c.post('/api/pedidos',json=alterado).status_code,403)
        with patch('src.backend.seguridad.time.time',return_value=time.time()+601):
            self.assertEqual(self.c.post('/api/pedidos',json=d).status_code,403)
        malo=dict(d,codigo_celular='00000000' if d['codigo_celular']!='00000000' else '11111111')
        for _ in range(5):
            self.assertEqual(self.c.post('/api/pedidos',json=malo).status_code,403)
        self.assertEqual(self.c.post('/api/pedidos',json=d).status_code,403)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reservas_stock').fetchone()[0],0)

    def test_limite_login_compartido_y_recuperacion(self):
        segunda=create_app(self.path).test_client()
        for c in [self.c,segunda,self.c,segunda,self.c]:
            self.assertEqual(c.post('/api/demo/sesion',json=dict(usuario='mira',clave='incorrecta')).status_code,401)
        self.assertEqual(self.login(segunda,'mira').status_code,429)
        self.assertEqual(self.login(segunda,'sur').status_code,200)
        with patch('src.backend.seguridad.time.time',return_value=time.time()+301):
            self.assertEqual(self.login(self.c,'mira').status_code,200)
        with patch('src.backend.seguridad.time.time',return_value=time.time()+301):
            segunda.set_cookie('session',self.c.get_cookie('session').value)
            self.assertEqual(segunda.get('/api/demo/inventario').status_code,200)

    def test_perfil_https_host_cookie_csp(self):
        with patch.dict(os.environ, dict(INKAFARMA_PERFIL='produccion',INKAFARMA_HOST='tienda.example',
                                        INKAFARMA_SESSION_SECRET=secrets.token_hex(32))):
            c=create_app(self.path).test_client()
            self.assertEqual(c.get('/',base_url='https://ajeno.example').status_code,400)
            self.assertEqual(c.get('/',base_url='http://tienda.example').status_code,400)
            r=c.post('/api/demo/sesion',base_url='https://tienda.example',json=dict(usuario='mira',clave=self.clave))
            self.assertEqual(r.status_code,200)
            for flag in ['Secure','HttpOnly','SameSite=Strict']:self.assertIn(flag,r.headers['Set-Cookie'])
            self.assertIn('max-age=',r.headers['Strict-Transport-Security'])
            self.assertIn("script-src 'self'",r.headers['Content-Security-Policy'])
