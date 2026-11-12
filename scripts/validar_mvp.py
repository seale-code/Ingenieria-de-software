"""S3-05: demostración técnica reproducible con datos temporales, sin SQL de avance.

python -m scripts.validar_mvp
El éxito comprueba los servicios disponibles; no acredita el cierre del Sprint 3.
"""
import json
import tempfile
from importlib.util import find_spec
from pathlib import Path
from uuid import uuid4

from src.backend.app import create_app
from src.backend.entregas_s3 import (
    obtener_historial_entrega, obtener_historial_pedido, registrar_entrega,
    registrar_fecha_entrega, registrar_fecha_salida,
)
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor
from src.database.database import initialize_database
from src.database.migrate_josue import migrar


def demostrar():
    """Crea y elimina su propia base. No recibe rutas a datos del usuario."""
    with tempfile.TemporaryDirectory(prefix='inkafarma-s3-') as directory:
        path = Path(directory) / 'demo.sqlite3'
        initialize_database(path, demo=True)
        migrar(path)
        iniciar_modulo(path)
        app = create_app(path)
        client = app.test_client()

        def get(url):
            response = client.get(url)
            if response.status_code != 200:
                raise RuntimeError(f'Error al consultar {url}: HTTP {response.status_code}')
            return response.json

        inicial = get('/api/catalogo?buscar=demo+a')['productos'][0]['cantidad']
        puntos = get('/api/pedidos/opciones')['puntos']
        norte = next(p for p in puntos if p['codigo'] == 'DEMO-NORTE')
        payload = dict(cliente='Cliente ficticio', latitud=norte['latitud'],
                       longitud=norte['longitud'], confirmacion_id=str(uuid4()),
                       items=[dict(producto_codigo='DEMO-A', cantidad=2)])
        response = client.post('/api/pedidos', json=payload)
        if response.status_code != 200:
            raise RuntimeError(f'Error al confirmar: HTTP {response.status_code}')
        pedido = response.json['pedido']
        repetido = client.post('/api/pedidos', json=payload)
        disponible = get('/api/catalogo?buscar=demo+a')['productos'][0]['cantidad']
        if disponible != inicial - 2 or repetido.json != response.json:
            raise RuntimeError('Disponibilidad o reintento de confirmación incoherentes')

        preparacion = {'estado': 'PENDIENTE', 'dependencia': 'PR #47 / tarea #16'}
        if find_spec('src.backend.preparacion_pedidos') is not None:
            from src.backend.preparacion_pedidos import (
                iniciar_preparacion_pedido, completar_preparacion_pedido,
            )
            iniciar_preparacion_pedido(pedido['pedido_id'], path)
            resultado = completar_preparacion_pedido(pedido['pedido_id'], path)
            if resultado['estado_nuevo'] != 'PREPARADO':
                raise RuntimeError('No se completó la preparación')
            preparacion = {'estado': 'VALIDADO', 'ultimo_estado': 'PREPARADO'}

        repartidor = registrar_repartidor('DEMO-REP', 'Repartidor ficticio', path)
        entrega = registrar_entrega(pedido['pedido_id'], repartidor['id'], db_path=path)
        registrar_fecha_salida(entrega['id'], db_path=path)
        fechada = registrar_fecha_entrega(entrega['id'], db_path=path)
        historial = obtener_historial_pedido(pedido['pedido_id'], path)
        seguimiento = {'estado': 'PENDIENTE', 'dependencia': 'PR #49 / tarea #15'}
        if '/api/seguimiento' in {rule.rule for rule in app.url_map.iter_rules()}:
            consulta = client.get('/api/seguimiento', headers={
                'X-Codigo-Pedido': 'WEB-' + payload['confirmacion_id']})
            if consulta.status_code != 200:
                raise RuntimeError(f'Error al consultar seguimiento: HTTP {consulta.status_code}')
            datos = consulta.json['pedido']
            estados = [r['estado'] for r in datos['historial']]
            if (datos['numero'] != pedido['pedido_id']
                    or datos['estado'] != historial[-1]['estado_nuevo']
                    or estados != [r['estado_nuevo'] for r in historial]):
                raise RuntimeError('Seguimiento incoherente con la preparación e historial')
            seguimiento = dict(estado='VALIDADO', numero=datos['numero'],
                ultimo_estado=datos['estado'], estados=estados)
        pendientes = ['#22: transiciones de reparto, permisos e incidencias',
                      '#17: aceptación del recorrido hasta ENTREGADO e integración web S3']
        if preparacion['estado'] == 'PENDIENTE':
            pendientes.insert(0, preparacion['dependencia'])
        if seguimiento['estado'] == 'PENDIENTE':
            pendientes.insert(0, seguimiento['dependencia'])
        return dict(
            alcance='VALIDACION_PARCIAL_NO_CIERRE_MVP',
            catalogo=dict(antes=inicial, reservado=2, disponible=disponible),
            confirmacion=dict(pedido_id=pedido['pedido_id'], reintento_sin_duplicar=True),
            preparacion=preparacion,
            seguimiento=seguimiento,
            entrega=dict(entrega_id=entrega['id'], fecha_salida=fechada['fecha_salida'],
                         fecha_recepcion=fechada['fecha_entrega'],
                         estado_pedido=fechada['estado_pedido'],
                         estado_entrega=fechada['estado_entrega']),
            estados_registrados=[r['estado_nuevo'] for r in historial],
            eventos_entrega=len(obtener_historial_entrega(entrega['id'], path)),
            pendientes=pendientes,
        )


if __name__ == '__main__':
    print(json.dumps(demostrar(), ensure_ascii=False, indent=2))
