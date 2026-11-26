"""Recorrido verificable en una base temporal; no modifica la tienda del usuario."""
from datetime import datetime
import json
from pathlib import Path
import tempfile
from uuid import uuid4

from scripts.iniciar_tienda import preparar_tienda
from scripts.fixture_sprints import create_fixture as create_app
from src.backend.inventario import consultar_inventario, registrar_movimiento
from src.backend.logistica import procesar_vencimientos
from src.database.database import connect_database


def main():
    with tempfile.TemporaryDirectory() as carpeta:
        path=Path(carpeta)/'validacion.sqlite3'; preparar_tienda(path)
        app=create_app(path,operations_key='acceso-interno-de-validacion-temporal')
        client=app.test_client()
        csrf=client.post('/api/demo/sesion',json={'clave':app.config['DEMO_KEY']}).json['csrf']

        def post(url,datos):
            respuesta=client.post(url,json=datos,headers={'X-CSRF-Token':csrf})
            assert respuesta.status_code==200,respuesta.json
            return respuesta.json

        def crear():
            items=[dict(producto_codigo='023735',cantidad=2)]
            cotizacion=post('/api/pedidos/cotizacion',dict(items=items))['cotizacion']
            return post('/api/pedidos',dict(cliente='Validación de logística',confirmacion_id=str(uuid4()),items=items,
                comercio=dict(cotizacion_id=cotizacion['cotizacion_id'],telefono='987654321',
                    direccion='Dirección de validación 123',distrito='MIRAFLORES')))['pedido']['pedido_id']

        def detalle(pedido): return client.get(f'/api/demo/pedidos/{pedido}').json['pedido']
        pedido=crear(); inicial=detalle(pedido); asignacion=inicial['logistica']['asignacion_id']; clave=str(uuid4())
        rechazo=dict(accion='rechazar',asignacion_id=asignacion,motivo='La sucursal declara falta de atención.',solicitud_id=clave)
        url=f'/api/demo/pedidos/{pedido}/acciones'
        cambio=post(url,rechazo)['resultado']; assert cambio['sucursal_codigo']=='SAN-ISIDRO'
        assert post(url,rechazo)['resultado']['reintento']
        reasignado=detalle(pedido); assert reasignado['comercio']==inicial['comercio']
        for accion in ['preparar','listo']:
            post(url,dict(accion=accion,asignacion_id=reasignado['logistica']['asignacion_id']))
        post(url,dict(accion='asignar',repartidor_id=1))
        for accion in ['salir','entregar']:
            post(url,dict(accion=accion)); assert post(url,dict(accion=accion))['resultado']['reintento']
        saldos=consultar_inventario(path)['existencias']
        assert next(f['fisico'] for f in saldos if f['producto_codigo']=='023735' and f['sucursal_codigo']=='MIRAFLORES')==18
        assert next(f['fisico'] for f in saldos if f['producto_codigo']=='023735' and f['sucursal_codigo']=='SAN-ISIDRO')==16
        entrada=registrar_movimiento('023735','SAN-ISIDRO','ENTRADA',5,'Recepción de mercadería según guía.',str(uuid4()),db_path=path)
        assert entrada['cantidad_nueva']==21
        ajuste=registrar_movimiento('023735','SAN-ISIDRO','AJUSTE',20,'Conteo físico documentado al cierre.',str(uuid4()),
                                    db_path=path,cantidad_esperada=21)
        assert ajuste['variacion']==-1
        pendiente=crear(); limite=detalle(pendiente)['logistica']['fecha_limite']
        vencidos=procesar_vencimientos(path,ahora=datetime.fromisoformat(limite.replace('Z','+00:00')))
        assert len(vencidos)==1 and vencidos[0]['reasignado']
        with connect_database(path,read_only=True) as db:
            assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert db.execute("SELECT count(*) FROM movimientos_inventario WHERE tipo='SALIDA_PEDIDO'").fetchone()[0]==1
        print(json.dumps(dict(resultado='LOGISTICA_VERIFICADA',reasignacion='MIRAFLORES → SAN-ISIDRO',
            entrega=detalle(pedido)['estado'],salidas_del_pedido=1,entrada=5,ajuste=-1,
            vencimientos_procesados=len(vencidos),integridad='ok',claves_foraneas='ok'),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
