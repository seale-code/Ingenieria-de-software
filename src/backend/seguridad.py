"""Identidad, límites compartidos y verificación telefónica de la tienda."""
from contextlib import contextmanager
import hashlib
import hmac
import re
import secrets
import time
from uuid import UUID

from flask import Blueprint, abort, current_app, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.database import connect_database

seguridad = Blueprint('seguridad', __name__)
ESQUEMA = """
CREATE TABLE IF NOT EXISTS operadores (
 usuario TEXT PRIMARY KEY, hash TEXT NOT NULL, sucursal TEXT REFERENCES sucursales(codigo),
 version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plazos_compra (pedido_id INTEGER PRIMARY KEY REFERENCES pedidos(id), limite TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ventanas (
 llave TEXT PRIMARY KEY, hasta INTEGER NOT NULL, total INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS verificaciones (
 solicitud TEXT PRIMARY KEY, telefono TEXT NOT NULL, hasta INTEGER NOT NULL,
 digest TEXT, intentos INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS auditoria_operaciones (
 id INTEGER PRIMARY KEY, usuario TEXT NOT NULL, ruta TEXT NOT NULL, metodo TEXT NOT NULL,
 accion TEXT, estado INTEGER, fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


@contextmanager
def escritura(path):
    with connect_database(path) as db:
        db.execute('BEGIN IMMEDIATE')
        yield db


def inicializar(path):
    with connect_database(path) as db:
        db.executescript(ESQUEMA)


def guardar_usuario(path, usuario, clave, sucursal=None):
    if not re.fullmatch(r'[a-z0-9._-]{2,64}', usuario) or len(clave) < 12:
        raise ValueError('Usuario de 2 a 64 caracteres y contraseña de al menos 12.')
    digest = generate_password_hash(clave)
    with escritura(path) as db:
        db.execute('INSERT INTO operadores VALUES(?,?,?,?) ON CONFLICT(usuario) DO UPDATE SET '
                   'hash=excluded.hash,sucursal=excluded.sucursal,version=excluded.version',
                   (usuario, digest, sucursal, secrets.token_hex(16)))


def gastar(db, llave, maximo, segundos):
    ahora = int(time.time())
    db.execute('DELETE FROM ventanas WHERE hasta<=?', (ahora,))
    cambio = db.execute('INSERT INTO ventanas VALUES(?,?,1) ON CONFLICT(llave) DO UPDATE '
                        'SET total=total+1 WHERE total<?', (llave, ahora+segundos, maximo))
    return cambio.rowcount == 1


def firma(texto):
    return hmac.new(current_app.secret_key.encode(), texto.encode(), hashlib.sha256).hexdigest()


def acceso(datos):
    usuario = datos.get('usuario')
    clave = datos.get('clave')
    if not isinstance(usuario, str) or not isinstance(clave, str) or len(usuario)>64 or len(clave)>256:
        abort(401)
    ip = request.remote_addr or 'local'
    path = current_app.config['DATABASE']
    with escritura(path) as db:
        permitido = gastar(db, firma('ip:'+ip), 60, 300) and gastar(db, firma(ip+'|'+usuario), 5, 300)
        cuenta = db.execute('SELECT * FROM operadores WHERE usuario=?', (usuario,)).fetchone()
    if not permitido:
        return jsonify(error='Demasiados intentos. Espera cinco minutos.'), 429, {'Retry-After':'300'}
    if not check_password_hash(cuenta['hash'] if cuenta else current_app.config['HASH_INACTIVO'], clave) or not cuenta:
        return jsonify(error='Credenciales incorrectas.'), 401
    session.clear()
    session.permanent = True
    session.update(usuario=usuario, version=cuenta['version'], demo_csrf=secrets.token_urlsafe(32))
    return jsonify(autenticado=True, csrf=session['demo_csrf'], sucursal=cuenta['sucursal'])


def cargar_cuenta():
    with connect_database(current_app.config['DATABASE'], read_only=True) as db:
        g.cuenta = db.execute('SELECT usuario,sucursal FROM operadores WHERE usuario=? AND version=?',
                              (session.get('usuario'), session.get('version'))).fetchone()
    return g.cuenta is not None


def auditar():
    with escritura(current_app.config['DATABASE']) as db:
        datos=request.get_json(silent=True)
        valor=datos.get('accion',datos.get('tipo')) if isinstance(datos,dict) else None
        acciones=('preparar','listo','rechazar','asignar','salir','entregar','cancelar','ENTRADA','AJUSTE')
        g.auditoria = db.execute('INSERT INTO auditoria_operaciones(usuario,ruta,metodo,accion) VALUES(?,?,?,?)',
                                 (g.cuenta['usuario'],request.path,request.method,valor if valor in acciones else None)).lastrowid


def cerrar_auditoria(respuesta):
    if getattr(g, 'auditoria', None):
        with escritura(current_app.config['DATABASE']) as db:
            db.execute('UPDATE auditoria_operaciones SET estado=? WHERE id=?',(respuesta.status_code,g.auditoria))
    return respuesta


@seguridad.post('/api/pedidos/verificacion')
def solicitar():
    datos = request.get_json(silent=True)
    if not isinstance(datos,dict):
        abort(400)
    telefono = datos.get('telefono')
    if not isinstance(telefono,str) or not re.fullmatch(r'9[0-9]{8}',telefono):
        abort(400)
    try:
        solicitud = str(UUID(str(datos.get('confirmacion_id'))))
    except ValueError:
        abort(400)
    ahora = int(time.time())
    with escritura(current_app.config['DATABASE']) as db:
        db.execute('DELETE FROM verificaciones WHERE hasta<=?',(ahora,))
        anterior=db.execute('SELECT telefono FROM verificaciones WHERE solicitud=?',(solicitud,)).fetchone()
        if anterior:
            if anterior['telefono'] != telefono:
                abort(409)
        else:
            if not gastar(db, firma('solicitud:'+str(request.remote_addr)), 6, 600):
                return jsonify(error='Espera diez minutos antes de solicitar otra llamada.'),429
            db.execute('INSERT INTO verificaciones(solicitud,telefono,hasta) VALUES(?,?,?)',
                       (solicitud,telefono,ahora+600))
    return jsonify(mensaje='Te llamaremos al celular indicado para darte el código.'),202


def emitir_codigo(solicitud):
    """Acción de consola; comunicar el código únicamente llamando al número registrado."""
    codigo = f'{secrets.randbelow(100_000_000):08d}'
    with escritura(current_app.config['DATABASE']) as db:
        fila=db.execute('SELECT telefono FROM verificaciones WHERE solicitud=? AND hasta>? AND digest IS NULL',
                        (solicitud,int(time.time()))).fetchone()
        if not fila:
            raise ValueError('Solicitud vencida, inexistente o ya atendida.')
        db.execute('UPDATE verificaciones SET digest=? WHERE solicitud=?',(firma(solicitud+codigo),solicitud))
    return fila['telefono'], codigo


def verificar_contacto(solicitud, telefono, codigo):
    if not isinstance(codigo,str) or not re.fullmatch(r'[0-9]{8}',codigo):
        return False
    with escritura(current_app.config['DATABASE']) as db:
        fila=db.execute('SELECT digest,intentos FROM verificaciones WHERE solicitud=? AND telefono=? AND hasta>?',
                        (solicitud,telefono,int(time.time()))).fetchone()
        if not fila or not fila['digest'] or fila['intentos']>=5:
            return False
        if hmac.compare_digest(fila['digest'],firma(solicitud+codigo)):
            return True
        db.execute('UPDATE verificaciones SET intentos=intentos+1 WHERE solicitud=?',(solicitud,))
        return False
