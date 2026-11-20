"""Aplicación Inkafarma: catálogo, pedidos, seguimiento y operaciones."""

import os
import sqlite3
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from src.backend.catalogo_busqueda import buscar_productos
from src.backend.pedidos_web import pedidos_web
from src.backend.seguimiento import seguimiento
from src.backend.operaciones_demo import operaciones
from src.database.database import DEFAULT_DATABASE, connect_database, get_stock
from src.backend.comercio import disponible, metadatos

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def _crear_base(db_path=None):
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="/assets")
    app.config["DATABASE"] = db_path or os.environ.get("INKAFARMA_DB", DEFAULT_DATABASE)
    app.config['DEMO_KEY'] = None

    @app.before_request
    def configuracion_completa():
        if not app.config.get('IDENTIDAD_PERSONAL') and not app.config.get('FIXTURE_HISTORICO'):
            return jsonify(error='Inicializa la tienda con create_app.'), 503
    app.secret_key = secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=2))

    app.config['MAX_CONTENT_LENGTH'] = 32768
    app.register_blueprint(pedidos_web)
    app.register_blueprint(seguimiento)
    app.register_blueprint(operaciones)

    @app.get('/operaciones')
    def panel_demo():
        if not (app.config.get('IDENTIDAD_PERSONAL') or app.config['DEMO_KEY']):
            from flask import abort
            abort(404)
        response = send_from_directory(FRONTEND, 'operaciones.html')
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/contexto')
    def contexto():
        return jsonify(operaciones_demo=bool(app.config.get('IDENTIDAD_PERSONAL') or app.config['DEMO_KEY']))

    @app.get('/ayuda')
    def ayuda():
        return send_from_directory(FRONTEND,'ayuda.html')

    @app.get('/privacidad')
    def privacidad():
        return send_from_directory(FRONTEND,'privacidad.html')

    @app.get("/seguimiento")
    def ver_seguimiento():
        response = send_from_directory(FRONTEND, "seguimiento.html")
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get('/pedido')
    def pedido():
        return send_from_directory(FRONTEND, 'pedido.html')

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND, "index.html")

    @app.after_request
    def no_cache(response):
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def db_error(error):
        app.logger.error("Consulta de catálogo no disponible: %s", type(error).__name__)
        return jsonify(error="No pudimos consultar los datos. Inténtalo de nuevo."), 503

    for error_type in (sqlite3.Error, ValueError, OSError):
        app.register_error_handler(error_type, db_error)

    @app.get("/api/filtros")
    def filtros():
        with connect_database(app.config["DATABASE"], read_only=True) as db:
            if disponible(db):
                categorias=[dict(row) for row in db.execute('''SELECT c.codigo,c.nombre FROM categorias c
                    WHERE EXISTS(SELECT 1 FROM productos p JOIN catalogo_comercial m ON m.producto_id=p.id
                        WHERE p.categoria_id=c.id) ORDER BY c.nombre,c.codigo''')]
                sucursales=[dict(row) for row in db.execute('''SELECT s.codigo,s.nombre FROM sucursales s
                    WHERE EXISTS(SELECT 1 FROM inventario i JOIN catalogo_comercial m ON m.producto_id=i.producto_id
                        WHERE i.sucursal_id=s.id) ORDER BY s.codigo''')]
                return jsonify(categorias=categorias,sucursales=sucursales)
            categorias = [dict(row) for row in db.execute(
                "SELECT codigo, nombre FROM categorias ORDER BY nombre, codigo"
            )]
            sucursales = [dict(row) for row in db.execute(
                "SELECT codigo, nombre FROM sucursales ORDER BY codigo"
            )]
        return jsonify(categorias=categorias, sucursales=sucursales)

    @app.get("/api/catalogo")
    def catalogo():
        solo = request.args.get("solo_disponibles", "false")
        if solo not in ("true", "false"):
            return jsonify(error="solo_disponibles debe ser true o false."), 400
        nombre = request.args.get("buscar", "").strip()
        categoria = request.args.get("categoria", "").strip()
        sucursal = request.args.get("sucursal", "").strip()
        path = app.config["DATABASE"]
        productos = buscar_productos(nombre, db_path=path)
        with connect_database(path, read_only=True) as db:
            extras=metadatos(db)
            comercial=disponible(db)
        if comercial:
            productos=[p for p in productos if p['producto_codigo'] in extras]
        if nombre and extras:
            termino=nombre.casefold()
            productos=[p for p in buscar_productos('',db_path=path) if p['producto_codigo'] in extras and (
                termino in p['producto'].casefold() or termino in extras[p['producto_codigo']]['marca'].casefold())]
        stock = get_stock(path, search="" if extras else nombre, category=categoria or None,
                          branch=sucursal or None, effective=True)
        por_producto = {}
        for fila in stock:
            por_producto.setdefault(fila["producto_codigo"], []).append(fila)
        resultado = []
        for producto in productos:
            if categoria and producto["categoria_codigo"] != categoria:
                continue
            filas = por_producto.get(producto["producto_codigo"], [])
            # Una sucursal filtra por inventario registrado, incluso si es cero.
            if sucursal and not filas:
                continue
            cantidad = sum(fila["cantidad"] for fila in filas) if filas else None
            if solo == "true" and not (cantidad is not None and cantidad > 0):
                continue
            resultado.append({**producto, "cantidad": cantidad, **extras.get(producto['producto_codigo'],{})})
        return jsonify(productos=resultado, total=len(resultado))

    @app.get("/api/productos/<codigo>/stock")
    def stock_producto(codigo):
        path = app.config["DATABASE"]
        with connect_database(path, read_only=True) as db:
            existe = db.execute("SELECT 1 FROM productos WHERE codigo = ?", (codigo,)).fetchone()
        if not existe:
            return jsonify(error="Producto no encontrado."), 404
        filas = [fila for fila in get_stock(path, effective=True)
                 if fila["producto_codigo"] == codigo]
        return jsonify(stock=filas)

    return app


def create_app(db_path=None):
    from tempfile import NamedTemporaryFile
    from werkzeug.security import generate_password_hash
    from src.backend.seguridad import inicializar, seguridad, cerrar_auditoria

    path = Path(db_path or os.environ.get('INKAFARMA_DB', 'data/inkafarma-comercial.sqlite3')).resolve()
    produccion = os.environ.get('INKAFARMA_PERFIL', 'local')
    if produccion not in ('local', 'produccion'):
        raise ValueError('Perfil no reconocido.')
    https = produccion == 'produccion'
    host = os.environ.get('INKAFARMA_HOST', '')
    secret = os.environ.get('INKAFARMA_SESSION_SECRET', '')
    if https and (not host or len(secret) < 32 or host.startswith('.') or '/' in host):
        raise ValueError('Producción requiere un host exacto y un secreto de sesión de al menos 32 caracteres.')
    inicializar(path)
    if not secret:
        destino = path.with_name(path.name + '.session-key')
        if not destino.exists():
            with NamedTemporaryFile(dir=path.parent) as temporal:
                temporal.write(secrets.token_hex(32).encode())
                temporal.flush()
                try:
                    os.link(temporal.name, destino)
                except FileExistsError:
                    pass
        secret = destino.read_text()
    if len(secret) < 32:
        raise ValueError('El secreto de sesión es demasiado corto.')
    app = _crear_base(path)
    app.config.update(IDENTIDAD_PERSONAL=True, SECRET_KEY=secret, SESSION_COOKIE_SECURE=https,
                      HASH_INACTIVO=generate_password_hash(secrets.token_hex(24)),
                      TRUSTED_HOSTS=[host] if https else ['localhost','127.0.0.1','[::1]'])
    app.register_blueprint(seguridad)
    app.after_request(cerrar_auditoria)

    @app.before_request
    def transporte():
        if not https and request.remote_addr not in ('127.0.0.1','::1'):
            return jsonify(error='El acceso de red requiere el perfil de producción.'), 403
        if https and not request.is_secure:
            return jsonify(error='Se requiere HTTPS.'), 400

    @app.after_request
    def cabeceras(respuesta):
        respuesta.headers['Content-Security-Policy'] = ("default-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self'")
        if https and request.is_secure:
            respuesta.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return respuesta
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)

