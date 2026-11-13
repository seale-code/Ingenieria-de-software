"""Integración S1-11: interfaz y API de consulta sobre la SQLite del equipo."""

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

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def create_app(db_path=None, *, demo_key=None):
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="/assets")
    app.config["DATABASE"] = db_path or os.environ.get("INKAFARMA_DB", DEFAULT_DATABASE)
    app.config['DEMO_KEY'] = demo_key if demo_key is not None else os.environ.get('INKAFARMA_DEMO_KEY')
    app.secret_key = secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=2))

    app.config['MAX_CONTENT_LENGTH'] = 32768
    app.register_blueprint(pedidos_web)
    app.register_blueprint(seguimiento)
    app.register_blueprint(operaciones)

    @app.get('/operaciones')
    def panel_demo():
        if not app.config['DEMO_KEY']:
            from flask import abort
            abort(404)
        response = send_from_directory(FRONTEND, 'operaciones.html')
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/contexto')
    def contexto():
        return jsonify(operaciones_demo=bool(app.config['DEMO_KEY']))

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
        stock = get_stock(path, search=nombre, category=categoria or None,
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
            resultado.append({**producto, "cantidad": cantidad})
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


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)

