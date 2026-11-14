"""Opciones de compra, cotización y confirmación de pedidos."""
import sqlite3

from flask import Blueprint, current_app, jsonify, request

from src.backend.catalogo_busqueda import buscar_productos
from src.backend.pedidos_integracion import ConflictoConfirmacion
from src.backend.pedidos_s2 import DatosInvalidos, ModuloNoInicializado, registrar_pedido
from src.database.database import connect_database
from src.backend.comercio import (DISTRITOS, disponible, metadatos, cotizar, validar_entrega,
    DatosComercialesInvalidos, CotizacionActualizada, ConfirmacionComercialReutilizada, ENVIO_CENTIMOS, ENVIO_GRATIS_DESDE)

pedidos_web = Blueprint('pedidos_web', __name__)


@pedidos_web.get('/api/pedidos/opciones')
def opciones():
    path = current_app.config['DATABASE']
    productos = buscar_productos(db_path=path)
    with connect_database(path, read_only=True) as db:
        puntos = [dict(row) for row in db.execute(
            'SELECT codigo,nombre,latitud,longitud FROM sucursales ORDER BY codigo')]
        comercial = disponible(db)
        extras = metadatos(db)
    productos=[dict(p,**extras.get(p['producto_codigo'],{})) for p in productos]
    if comercial:
        productos=[p for p in productos if p['producto_codigo'] in extras]
    return jsonify(productos=productos, puntos=puntos, comercial=comercial,
        politica_envio=dict(costo_centimos=ENVIO_CENTIMOS,gratis_desde_centimos=ENVIO_GRATIS_DESDE),
        distritos=[dict(codigo=k,nombre=v[0]) for k,v in DISTRITOS.items()] if comercial else [])


@pedidos_web.post('/api/pedidos/cotizacion')
def cotizacion():
    datos=request.get_json(silent=True)
    if not isinstance(datos,dict) or set(datos)!={'items'}:
        return jsonify(error='Envía los productos que deseas revisar.'),400
    try:
        with connect_database(current_app.config['DATABASE'],read_only=True) as db:
            db.execute('BEGIN')
            resultado=cotizar(db,datos['items'])
        return jsonify(cotizacion=resultado)
    except DatosComercialesInvalidos as error:
        return jsonify(error=str(error)),400


@pedidos_web.post('/api/pedidos')
def confirmar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict) or not isinstance(datos.get('confirmacion_id'), str):
        return jsonify(error='Envía un pedido con un identificador de confirmación válido.'), 400
    try:
        with connect_database(current_app.config['DATABASE'],read_only=True) as db:
            es_comercial=disponible(db)
        comercial=None
        if es_comercial:
            comercial=validar_entrega(datos.get('comercio'))
            zona=DISTRITOS[comercial['distrito']]
            datos=dict(datos,latitud=zona[1],longitud=zona[2])
        resultado = registrar_pedido(datos, current_app.config['DATABASE'],
                                     confirmacion_id=datos['confirmacion_id'],comercial=comercial)
    except DatosComercialesInvalidos as error:
        return jsonify(error=str(error)),400
    except CotizacionActualizada as error:
        return jsonify(error=str(error),codigo='PRECIO_ACTUALIZADO'),409
    except DatosInvalidos as error:
        return jsonify(error=str(error)), 400
    except (ConflictoConfirmacion,ConfirmacionComercialReutilizada) as error:
        return jsonify(error=str(error), codigo='CONFIRMACION_REUTILIZADA'), 409
    except (ModuloNoInicializado, sqlite3.Error, OSError, ValueError) as error:
        current_app.logger.error('Confirmación no disponible: %s', type(error).__name__)
        return jsonify(error='No pudimos comprobar la confirmación. Reintenta con el mismo pedido.'), 503
    if resultado['estado'] == 'SIN_ASIGNAR':
        return jsonify(error=resultado['motivo'], codigo=resultado['motivo_codigo']), 409
    return jsonify(pedido=resultado), 200
