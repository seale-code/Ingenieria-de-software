"""Contratos HTTP v6: autorización del panel y seguimiento público sin datos privados."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.logistica import fecha_utc
from src.backend.pedidos_s2 import configurar_capacidad
from src.database.database import connect_database


class LogisticaWebTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'web.sqlite3'; preparar_tienda(self.path)
        self.app=create_app(self.path,operations_key='acceso-de-pruebas-operaciones'); self.app.testing=True
        self.client=self.app.test_client()
        quote=self.client.post('/api/pedidos/cotizacion',json={'items':[{'producto_codigo':'023735','cantidad':2}]}).json['cotizacion']
        self.payload=dict(cliente='Nombre privado',confirmacion_id=str(uuid4()),items=[{'producto_codigo':'023735','cantidad':2}],
            comercio=dict(cotizacion_id=quote['cotizacion_id'],telefono='987654321',direccion='Calle privada 123',distrito='MIRAFLORES'))
        self.order=self.client.post('/api/pedidos',json=self.payload).json['pedido']['pedido_id']
        self.csrf=self.client.post('/api/demo/sesion',json={'clave':self.app.config['DEMO_KEY']}).json['csrf']

    def post(self,url,data):
        return self.client.post(url,json=data,headers={'X-CSRF-Token':self.csrf})

    def detalle(self):
        return self.client.get(f'/api/demo/pedidos/{self.order}').json['pedido']

    def accion(self,accion,**extra):
        return self.post(f'/api/demo/pedidos/{self.order}/acciones',dict(accion=accion,**extra))

    def rechazo(self,**extra):
        data=dict(asignacion_id=self.detalle()['logistica']['asignacion_id'],motivo='No hay existencias físicas para el pedido.',solicitud_id=str(uuid4()))
        data.update(extra); return self.accion('rechazar',**data)

    def seguimiento(self):
        return self.client.get('/api/seguimiento',headers={'X-Codigo-Pedido':'WEB-'+self.payload['confirmacion_id']}).json['pedido']

    def test_inventario_y_procesamiento_requieren_sesion_csrf_y_origen(self):
        ajeno=self.app.test_client()
        self.assertEqual(ajeno.get('/api/demo/inventario').status_code,401)
        for url in ['/api/demo/inventario/movimientos','/api/demo/reservas/procesar']:
            self.assertEqual(ajeno.post(url,json={}).status_code,401)
            self.assertEqual(self.client.post(url,json={}).status_code,403)
            self.assertEqual(self.client.post(url,json={},headers={'X-CSRF-Token':self.csrf,'Origin':'https://otro.example'}).status_code,403)
        apagado=create_app(self.path,operations_key='').test_client()
        self.assertEqual(apagado.get('/api/demo/inventario').status_code,404)

    def test_preparacion_v6_exige_asignacion_vigente(self):
        self.assertEqual(self.accion('preparar').status_code,409)
        self.assertEqual(self.accion('preparar',asignacion_id=True).status_code,409)
        generacion=self.detalle()['logistica']['asignacion_id']; self.rechazo()
        self.assertEqual(self.accion('preparar',asignacion_id=generacion).status_code,409)
        actual=self.detalle()['logistica']['asignacion_id']
        self.assertEqual(self.accion('preparar',asignacion_id=actual).status_code,200)
        self.assertIsNotNone(self.detalle()['logistica']['aceptada_en'])

    def test_reasigna_con_importes_direccion_codigo_e_idempotencia_intactos(self):
        antes=self.detalle(); generacion=antes['logistica']['asignacion_id']; clave=str(uuid4())
        respuesta=self.rechazo(asignacion_id=generacion,solicitud_id=clave)
        self.assertEqual(respuesta.status_code,200,respuesta.json)
        despues=self.detalle()
        self.assertEqual(despues['sucursal_codigo'],'SAN-ISIDRO')
        self.assertEqual(despues['comercio'],antes['comercio']); self.assertEqual(despues['pedido_codigo'],antes['pedido_codigo'])
        replay=self.client.post('/api/pedidos',json=self.payload)
        self.assertEqual(replay.status_code,200); self.assertEqual(replay.json['pedido']['pedido_id'],self.order)
        self.assertEqual(replay.json['pedido']['sucursal_codigo'],'SAN-ISIDRO')
        segundo=self.rechazo(asignacion_id=generacion,solicitud_id=clave)
        self.assertTrue(segundo.json['resultado']['reintento']); self.assertEqual(self.detalle(),despues)

    def test_seguimiento_informa_cambio_sin_motivos_internos_ni_contactos(self):
        secreto='Inventario privado con discrepancia 123-ABC.'
        self.assertEqual(self.rechazo(motivo=secreto).status_code,200)
        publico=self.seguimiento()
        self.assertEqual(publico['sucursal'],'San Isidro'); self.assertIn('Reasignamos',publico['mensaje'])
        self.assertEqual(len(publico['cambios_sucursal']),1)
        for valor in [secreto,'987654321','Calle privada','Nombre privado','actor_id','solicitud_id']:
            self.assertNotIn(valor,str(publico))

    def test_cancelacion_sin_alternativa_tiene_mensaje_y_liberacion(self):
        for codigo in ['SAN-ISIDRO','SURCO']: configurar_capacidad(codigo,0,self.path)
        self.assertEqual(self.rechazo().status_code,200)
        publico=self.seguimiento()
        self.assertEqual(publico['estado'],'CANCELADO'); self.assertIn('ninguna sucursal alternativa',publico['mensaje'])
        detalle=self.detalle()
        self.assertEqual(detalle['items'][0]['estado_reserva'],'LIBERADA')
        self.assertIn('cancelado',detalle['incidencias'][0]['resolucion'])

    def test_cancelar_manualmente_despues_de_reasignar_no_anuncia_otra_reasignacion(self):
        self.rechazo(); self.accion('cancelar')
        self.assertEqual(self.seguimiento()['mensaje'],'El pedido fue cancelado.')

    def test_operador_no_puede_enviar_rol_actor_o_causa_del_sistema(self):
        for extra in [dict(rol='SISTEMA'),dict(actor_id=1),dict(por_vencimiento=True)]:
            self.assertEqual(self.rechazo(**extra).status_code,400)
        self.assertEqual(len(self.detalle()['logistica']['historial']),1)

    def test_movimiento_http_respetando_reservas_reintentos_y_saldo_obsoleto(self):
        url='/api/demo/inventario/movimientos'
        datos=dict(producto_codigo='023735',sucursal_codigo='MIRAFLORES',tipo='ENTRADA',cantidad=3,
            motivo='Recepción con guía de entrada 001-024.',solicitud_id=str(uuid4()))
        respuesta=self.post(url,datos); self.assertEqual(respuesta.status_code,200,respuesta.json)
        self.assertEqual(respuesta.json['movimiento']['cantidad_nueva'],21)
        self.assertTrue(self.post(url,datos).json['movimiento']['reintento'])
        ajuste=dict(datos,tipo='AJUSTE',cantidad=1,cantidad_esperada=21,solicitud_id=str(uuid4()))
        self.assertEqual(self.post(url,ajuste).status_code,409)
        ajuste.update(cantidad=20,cantidad_esperada=18)
        self.assertEqual(self.post(url,ajuste).status_code,409)
        data=self.client.get('/api/demo/inventario').json
        fila=next(r for r in data['existencias'] if r['producto_codigo']=='023735' and r['sucursal_codigo']=='MIRAFLORES')
        self.assertEqual((fila['fisico'],fila['reservado'],fila['disponible']),(21,2,19))
        self.assertEqual(self.post(url,dict(datos,rol='ADMINISTRADOR')).status_code,400)

    def test_procesar_vencidos_por_http_y_repetir_no_mueve_otro_intento(self):
        with connect_database(self.path) as db:
            db.execute('UPDATE control_reservas SET fecha_limite=? WHERE pedido_id=?',
                (fecha_utc(datetime.now(timezone.utc)-timedelta(seconds=1)),self.order))
        primero=self.post('/api/demo/reservas/procesar',{})
        self.assertEqual(primero.status_code,200,primero.json); self.assertEqual(primero.json['procesados'],1)
        self.assertEqual(self.post('/api/demo/reservas/procesar',{}).json['procesados'],0)
        self.assertEqual(self.detalle()['sucursal_codigo'],'SAN-ISIDRO')

    def test_error_de_persistencia_es_generico_y_no_confirma_exito(self):
        with patch('src.backend.operaciones_demo.registrar_movimiento',side_effect=sqlite3.OperationalError('ruta/privada')):
            response=self.post('/api/demo/inventario/movimientos',dict(producto_codigo='023735',sucursal_codigo='MIRAFLORES',
                tipo='ENTRADA',cantidad=1,motivo='Recepción de mercadería.',solicitud_id=str(uuid4())))
        self.assertEqual(response.status_code,503); self.assertNotIn('ruta/privada',str(response.json))


if __name__=='__main__': unittest.main()
