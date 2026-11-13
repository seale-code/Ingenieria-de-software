"""Panel local del expositor: habilitación explícita, sesión y protección CSRF.

La sesión representa al operador de la demostración, que simula las acciones
de sucursal, repartidor y soporte. No es autenticación de empleados reales.
Los roles/actores para los servicios se determinan en el servidor.
"""
import hmac
import secrets
import sqlite3

from flask import Blueprint, abort, current_app, jsonify, request, session

from src.backend.entregas_s3 import DatosEntregaInvalidos, EntregaDuplicada, registrar_entrega
from src.backend.preparacion_pedidos import (
    ErrorPreparacionPedido,
    completar_preparacion_pedido, iniciar_preparacion_pedido, obtener_pedido_preparacion,
)
from src.backend.repartidores_s3 import listar_repartidores
from src.backend.reparto_integrado import avanzar_reparto
from src.backend.soporte_pedidos_s3 import (
    ErrorSoportePedido,
    actualizar_estado_incidencia, cancelar_pedido, listar_incidencias, registrar_incidencia,
)
from src.database.database import connect_database

operaciones = Blueprint('operaciones_demo', __name__)


def _clave():
    return current_app.config.get('DEMO_KEY')


def _sesion_valida():
    return _clave() and session.get('demo_autorizada') is True


@operaciones.before_request
def proteger_panel():
    if not _clave():
        abort(404)
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('Origin')
        if origin and origin != request.host_url.rstrip('/'):
            return jsonify(error='El origen de la solicitud no está permitido.'), 403
        if not request.is_json:
            return jsonify(error='Envía la solicitud como JSON.'), 400
    if request.endpoint == 'operaciones_demo.sesion_demo':
        if request.method in ('GET', 'POST'):
            return None
    if not _sesion_valida():
        return jsonify(error='Inicia la sesión de demostración.'), 401
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        token = request.headers.get('X-CSRF-Token', '')
        esperado = session.get('demo_csrf', '')
        if not esperado or not hmac.compare_digest(token.encode(), esperado.encode()):
            return jsonify(error='La sesión cambió. Vuelve a iniciar sesión.'), 403


def datos_invalidos(error):
    return jsonify(error=str(error)), 409


for tipo in (ErrorPreparacionPedido, ErrorSoportePedido, DatosEntregaInvalidos, EntregaDuplicada):
    operaciones.register_error_handler(tipo, datos_invalidos)


@operaciones.errorhandler(400)
def solicitud_invalida(error):
    return jsonify(error='Los campos enviados no son válidos.'), 400


@operaciones.errorhandler(LookupError)
def no_encontrado(error):
    return jsonify(error=str(error)), 404


@operaciones.errorhandler(sqlite3.Error)
@operaciones.errorhandler(OSError)
def no_disponible(error):
    current_app.logger.warning('Operaciones demo no disponibles: %s', type(error).__name__)
    return jsonify(error='No pudimos completar la operación. Actualiza para comprobar el estado.'), 503


def _datos(campos, obligatorios=()):
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or set(datos) - set(campos) or not set(obligatorios) <= set(datos):
        abort(400, description='Los campos enviados no son válidos.')
    return datos


@operaciones.route('/api/demo/sesion', methods=['GET', 'POST', 'DELETE'])
def sesion_demo():
    if request.method == 'POST':
        datos = _datos({'clave'}, {'clave'})
        clave = datos['clave']
        if not isinstance(clave, str) or not hmac.compare_digest(clave.encode(), _clave().encode()):
            return jsonify(error='La clave de demostración no es correcta.'), 401
        session.clear()
        session.permanent = True
        session['demo_autorizada'] = True
        session['demo_csrf'] = secrets.token_urlsafe(32)
    elif request.method == 'DELETE':
        session.clear()
    return jsonify(autenticado=bool(_sesion_valida()), csrf=session.get('demo_csrf') if _sesion_valida() else None)


@operaciones.get('/api/demo/pedidos')
def bandeja():
    with connect_database(current_app.config['DATABASE'], read_only=True) as db:
        db.execute('BEGIN')
        filas = db.execute("""SELECT p.id AS pedido_id, p.estado, p.fecha_creacion,
            s.nombre AS sucursal_nombre, sol.cliente,
            (SELECT sum(cantidad) FROM detalles_pedido WHERE pedido_id=p.id) AS unidades
            FROM pedidos p JOIN sucursales s ON s.id=p.sucursal_id
            LEFT JOIN s2_solicitudes sol ON sol.pedido_id=p.id
            ORDER BY p.id DESC LIMIT 100""").fetchall()
        estados = {r['estado']: r['n'] for r in db.execute('SELECT estado,count(*) n FROM pedidos GROUP BY estado')}
        abiertas = db.execute("SELECT count(*) FROM incidencias_pedido WHERE estado!='RESUELTA'").fetchone()[0]
    return jsonify(pedidos=[dict(r) for r in filas], repartidores=listar_repartidores(True, current_app.config['DATABASE']),
                   resumen=dict(activos=sum(n for e, n in estados.items() if e not in ('ENTREGADO', 'CANCELADO')),
                                en_camino=estados.get('EN_CAMINO', 0), entregados=estados.get('ENTREGADO', 0), incidencias=abiertas))


@operaciones.get('/api/demo/pedidos/<int:pedido_id>')
def detalle(pedido_id):
    path = current_app.config['DATABASE']
    pedido = obtener_pedido_preparacion(pedido_id, path)
    with connect_database(path, read_only=True) as db:
        entrega = db.execute('''SELECT e.*,r.nombre AS repartidor_nombre FROM entregas e
            JOIN repartidores r ON r.id=e.repartidor_id WHERE e.pedido_id=?''', (pedido_id,)).fetchone()
    pedido['entrega'] = dict(entrega) if entrega else None
    pedido['incidencias'] = listar_incidencias('ADMINISTRADOR', pedido_id=pedido_id, db_path=path)
    return jsonify(pedido=pedido)


@operaciones.post('/api/demo/pedidos/<int:pedido_id>/acciones')
def actuar(pedido_id):
    datos = _datos({'accion', 'repartidor_id'}, {'accion'})
    accion = datos['accion']
    path = current_app.config['DATABASE']
    if accion == 'preparar':
        resultado = iniciar_preparacion_pedido(pedido_id, path)
    elif accion == 'listo':
        resultado = completar_preparacion_pedido(pedido_id, path)
    elif accion == 'asignar':
        pedido = obtener_pedido_preparacion(pedido_id, path)
        if pedido['estado'] != 'PREPARADO':
            return jsonify(error='Termina la preparación antes de asignar el reparto.'), 409
        resultado = registrar_entrega(pedido_id, datos.get('repartidor_id'), db_path=path)
    elif accion in ('salir', 'entregar'):
        with connect_database(path, read_only=True) as db:
            entrega = db.execute('SELECT repartidor_id FROM entregas WHERE pedido_id=?', (pedido_id,)).fetchone()
        if entrega is None:
            return jsonify(error='Asigna un repartidor primero.'), 409
        resultado = avanzar_reparto(pedido_id, 'EN_CAMINO' if accion == 'salir' else 'ENTREGADO',
                                  'REPARTIDOR', entrega['repartidor_id'], path)
    elif accion == 'cancelar':
        resultado = cancelar_pedido(pedido_id, 'ADMINISTRADOR', db_path=path)
    else:
        return jsonify(error='La acción no está disponible.'), 400
    return jsonify(resultado=resultado)


@operaciones.post('/api/demo/pedidos/<int:pedido_id>/incidencias')
def reportar(pedido_id):
    datos = _datos({'categoria', 'descripcion'}, {'categoria', 'descripcion'})
    incidencia = registrar_incidencia(pedido_id, datos['categoria'], datos['descripcion'],
                                    'ADMINISTRADOR', db_path=current_app.config['DATABASE'])
    return jsonify(incidencia=incidencia), 201


@operaciones.post('/api/demo/incidencias/<int:incidencia_id>/atender')
def atender(incidencia_id):
    datos = _datos({'estado', 'resolucion'}, {'estado'})
    incidencia = actualizar_estado_incidencia(incidencia_id, datos['estado'], 'ADMINISTRADOR',
        resolucion=datos.get('resolucion'), db_path=current_app.config['DATABASE'])
    return jsonify(incidencia=incidencia)
