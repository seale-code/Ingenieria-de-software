"""S3-05: recorrido completo HTTP + servicios sobre una SQLite temporal v4.

python -m scripts.validar_mvp
La validación técnica no sustituye la revisión/aceptación del equipo.
"""
import json
import secrets
import tempfile
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor
from src.database.database import initialize_database, connect_database, get_stock
from src.database.migrate_josue import migrar


def demostrar():
    """Crea y elimina su propia base; no acepta rutas a datos del usuario."""
    with tempfile.TemporaryDirectory(prefix='inkafarma-s3-') as directory:
        path = Path(directory) / 'demo.sqlite3'
        initialize_database(path,demo=True)
        migrar(path,hasta=4)
        iniciar_modulo(path)
        key = secrets.token_urlsafe(24)
        app = create_app(path,demo_key=key)
        client = app.test_client()

        def check(response,expected=200):
            if response.status_code != expected:
                raise RuntimeError(f'La operación falló: HTTP {response.status_code}')
            return response.json

        def stock(effective=True):
            return next(r['cantidad'] for r in get_stock(path,effective=effective)
                        if r['producto_codigo']=='DEMO-A' and r['sucursal_codigo']=='DEMO-NORTE')

        csrf = check(client.post('/api/demo/sesion',json={'clave':key}))['csrf']
        def post(url,body,expected=200):
            return check(client.post(url,json=body,headers={'X-CSRF-Token':csrf}),expected)

        initial = stock()
        payload = dict(cliente='Cliente ficticio',latitud=-12.0,longitud=-77.05,
            confirmacion_id=str(uuid4()),items=[dict(producto_codigo='DEMO-A',cantidad=2)])
        confirmation = post('/api/pedidos',payload)
        repeated = post('/api/pedidos',payload)
        pedido = confirmation['pedido']['pedido_id']
        code = 'WEB-'+payload['confirmacion_id']
        reserved = stock()
        if repeated != confirmation or reserved != initial-2:
            raise RuntimeError('La confirmación o su reintento alteró la reserva.')
        driver = registrar_repartidor('DEMO-REP','Repartidor ficticio',path)
        def action(name,**extra):
            return post(f'/api/demo/pedidos/{pedido}/acciones',dict(accion=name,**extra))
        action('preparar'); action('listo'); action('asignar',repartidor_id=driver['id'])
        action('salir')
        during = check(client.get('/api/demo/pedidos/'+str(pedido)))['pedido']
        action('salir')  # Reintento del mismo paso: sin segundo consumo ni evento.
        if check(client.get('/api/demo/pedidos/'+str(pedido)))['pedido'] != during:
            raise RuntimeError('El reintento de salida duplicó efectos.')
        action('entregar'); action('entregar')
        incident = post(f'/api/demo/pedidos/{pedido}/incidencias',dict(
            categoria='RETRASO',descripcion='Problema ficticio para comprobar el soporte.'),201)['incidencia']['id']
        post(f'/api/demo/incidencias/{incident}/atender',dict(estado='EN_REVISION'))
        post(f'/api/demo/incidencias/{incident}/atender',dict(estado='RESUELTA',resolucion='Solución ficticia documentada.'))
        detail = check(client.get('/api/demo/pedidos/'+str(pedido)))['pedido']
        tracking = check(client.get('/api/seguimiento',headers={'X-Codigo-Pedido':code}))['pedido']
        expected = ['ASIGNADO','EN_PREPARACION','PREPARADO','EN_CAMINO','ENTREGADO']
        if ([h['estado'] for h in tracking['historial']] != expected or
                tracking['estado'] != 'ENTREGADO' or detail['entrega']['estado'] != 'ENTREGADA' or
                stock() != 3 or stock(False) != 3 or detail['incidencias'][0]['estado'] != 'RESUELTA'):
            raise RuntimeError('Entrega, seguimiento, incidencia o stock incoherentes.')
        # Una segunda solicitud cancelada libera disponibilidad sin consumo físico.
        cancellation = post('/api/pedidos',dict(payload,confirmacion_id=str(uuid4()),
                            items=[dict(producto_codigo='DEMO-A',cantidad=1)]))['pedido']['pedido_id']
        post(f'/api/demo/pedidos/{cancellation}/acciones',dict(accion='cancelar'))
        if stock() != 3 or stock(False) != 3:
            raise RuntimeError('La cancelación no restauró la disponibilidad.')
        with connect_database(path,read_only=True) as db:
            integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
            foreign_keys = db.execute('PRAGMA foreign_key_check').fetchall()
        if integrity != 'ok' or foreign_keys:
            raise RuntimeError('La base no superó la comprobación de integridad.')
        return dict(alcance='RECORRIDO_TECNICO_MVP_COMPLETO',schema=4,
            catalogo=dict(antes=initial,tras_reserva=reserved,tras_entrega=stock(),fisico=stock(False)),
            confirmacion=dict(pedido_id=pedido,reintento_sin_duplicar=True),
            estados_registrados=expected,
            entrega=dict(estado_pedido=detail['estado'],estado_entrega=detail['entrega']['estado'],
                         salida=detail['entrega']['fecha_salida'],recepcion=detail['entrega']['fecha_entrega']),
            soporte='RESUELTA',cancelacion='RESERVA_LIBERADA_SIN_CONSUMO',
            integridad=integrity,aceptacion_equipo='PENDIENTE_DE_REVISION')


if __name__ == '__main__':
    print(json.dumps(demostrar(),ensure_ascii=False,indent=2))
