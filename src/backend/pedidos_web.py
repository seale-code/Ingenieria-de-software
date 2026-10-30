"""S2-02 / #20: opciones y confirmación para el formulario académico."""
import sqlite3

from flask import Blueprint, current_app, jsonify, request

from src.backend.catalogo_busqueda import buscar_productos
from src.backend.pedidos_integracion import ConflictoConfirmacion
from src.backend.pedidos_s2 import DatosInvalidos, ModuloNoInicializado, registrar_pedido
from src.database.database import connect_database

pedidos_web = Blueprint('pedidos_web', __name__)


@pedidos_web.get('/api/pedidos/opciones')
def opciones():
    path = current_app.config['DATABASE']
    productos = buscar_productos(db_path=path)
    with connect_database(path, read_only=True) as db:
        puntos = [dict(row) for row in db.execute(
            'SELECT codigo,nombre,latitud,longitud FROM sucursales ORDER BY codigo')]
    return jsonify(productos=productos, puntos=puntos)


@pedidos_web.post('/api/pedidos')
def confirmar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or not isinstance(datos.get('confirmacion_id'), str):
        return jsonify(error='Envía un pedido con un identificador de confirmación válido.'), 400
    try:
        resultado = registrar_pedido(datos, current_app.config['DATABASE'],
                                     confirmacion_id=datos['confirmacion_id'])
    except DatosInvalidos as error:
        return jsonify(error=str(error)), 400
    except ConflictoConfirmacion as error:
        return jsonify(error=str(error), codigo='CONFIRMACION_REUTILIZADA'), 409
    except (ModuloNoInicializado, sqlite3.Error, OSError, ValueError) as error:
        current_app.logger.error('Confirmación no disponible: %s', type(error).__name__)
        return jsonify(error='No pudimos comprobar la confirmación. Reintenta con el mismo pedido.'), 503
    if resultado['estado'] == 'SIN_ASIGNAR':
        return jsonify(error=resultado['motivo'], codigo=resultado['motivo_codigo']), 409
    return jsonify(pedido=resultado), 200
