"""S3-02: consulta de solo lectura mediante el código privado del pedido."""
import re
import sqlite3
from flask import Blueprint, current_app, jsonify, request
from src.database.database import connect_database
from src.backend.logistica import obtener_logistica

seguimiento = Blueprint('seguimiento', __name__)
ESTADOS = {
    'REGISTRADO': ('Registrado', 'Recibimos tu pedido.'),
    'ASIGNADO': ('Asignado', 'Una sucursal atenderá tu pedido.'),
    'EN_PREPARACION': ('En preparación', 'Estamos preparando tus productos.'),
    'PREPARADO': ('Preparado', 'Tu pedido está listo para el siguiente paso.'),
    'EN_CAMINO': ('En camino', 'Tu pedido está en camino.'),
    'ENTREGADO': ('Entregado', 'La entrega de tu pedido fue confirmada.'),
    'CANCELADO': ('Cancelado', 'El pedido fue cancelado.'),
}

@seguimiento.get('/api/seguimiento')
def consultar():
    # El ID numérico no autoriza consultas. Se necesita el código completo.
    codigo = request.headers.get('X-Codigo-Pedido', '').strip()
    if not re.fullmatch(r'(?:WEB-[0-9a-fA-F-]{36}|S2-[0-9a-fA-F]{32})', codigo):
        return jsonify(error='Introduce el código completo que recibiste al confirmar el pedido.'), 400
    try:
        with connect_database(current_app.config['DATABASE'], read_only=True) as db:
            db.execute('BEGIN')  # Estado e historial de la misma instantánea.
            pedido = db.execute("""SELECT p.id, p.estado, p.fecha_creacion, s.nombre AS sucursal
                FROM pedidos p JOIN sucursales s ON s.id=p.sucursal_id
                WHERE p.codigo=?""", (codigo,)).fetchone()
            if pedido is None:
                return jsonify(error='No encontramos ese pedido. Revisa el código e inténtalo de nuevo.'), 404
            historial = db.execute("""SELECT estado_nuevo, fecha_cambio FROM historial_estados
                WHERE pedido_id=? ORDER BY fecha_cambio, id""", (pedido['id'],)).fetchall()
            etiqueta, mensaje = ESTADOS.get(pedido['estado'], ('En actualización', 'Estamos actualizando tu pedido.'))
            logistica = obtener_logistica(db, pedido['id'])
            cambios = []
            if logistica:
                for evento in logistica['historial']:
                    if evento['causa'] in ('INICIAL', 'MIGRACION'):
                        continue
                    destino = evento['sucursal_destino']
                    texto = (f"Reasignamos tu pedido a {destino} para continuar la atención." if destino
                             else 'Cancelamos el pedido porque ninguna sucursal alternativa puede atenderlo. Las reservas fueron liberadas.')
                    cambios.append(dict(fecha=evento['fecha'], mensaje=texto))
                if cambios and (pedido['estado']=='ASIGNADO' or
                    (pedido['estado']=='CANCELADO' and logistica['historial'][-1]['sucursal_destino_id'] is None)):
                    mensaje = cambios[-1]['mensaje']
            resultado = dict(numero=pedido['id'], estado=pedido['estado'],
                etiqueta=etiqueta, mensaje=mensaje, sucursal=pedido['sucursal'],
                historial=[dict(estado=h['estado_nuevo'], fecha=h['fecha_cambio'],
                    etiqueta=ESTADOS.get(h['estado_nuevo'], ('En actualización', ''))[0]) for h in historial])
            if logistica:
                resultado['cambios_sucursal'] = cambios
            return jsonify(pedido=resultado)
    except (sqlite3.Error, OSError, ValueError):
        current_app.logger.warning('Seguimiento temporalmente no disponible')
        return jsonify(error='No pudimos consultar el seguimiento. Inténtalo de nuevo en unos momentos.'), 503
