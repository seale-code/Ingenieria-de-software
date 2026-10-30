"""Integración S1-11: interfaz y API de consulta sobre la SQLite del equipo."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from src.backend.catalogo_busqueda import buscar_productos
from src.database.database import DEFAULT_DATABASE, connect_database, get_stock

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def create_app(db_path=None):
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="/assets")
    app.config["DATABASE"] = db_path or os.environ.get("INKAFARMA_DB", DEFAULT_DATABASE)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND, "index.html")

    @app.after_request
    def no_cache(response):
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
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
                          branch=sucursal or None)
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
        filas = [fila for fila in get_stock(path) if fila["producto_codigo"] == codigo]
        return jsonify(stock=filas)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
