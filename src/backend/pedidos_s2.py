"""Registro transaccional de pedidos y asignación de sucursal (issue #18).

Uso desde la raíz del repositorio original:
    from src.backend.pedidos_s2 import iniciar_modulo, configurar_capacidad, registrar_pedido

El Sprint 1 ya proporciona src.database.database, productos, sucursales e inventario.
No requiere Flask ni bibliotecas de terceros. No es una API pública autenticada.
"""

from __future__ import annotations

from math import isfinite
from pathlib import Path
import sqlite3

from src.database.database import DEFAULT_DATABASE, connect_database
from src.backend.asignacion_sucursal import distancia_km, ordenar_candidatas

SCRIPT = Path(__file__).with_name("pedidos_s2_schema.sql")


class DatosInvalidos(ValueError):
    """La solicitud no cumple validaciones de usuario o catálogo."""


class ModuloNoInicializado(RuntimeError):
    """Falta ejecutar iniciar_modulo() sobre esta base."""


def _entero_positivo(valor: object, *, campo: str, permitir_cero: bool = False) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < (0 if permitir_cero else 1):
        raise DatosInvalidos(f"{campo} debe ser un número entero {'no negativo' if permitir_cero else 'mayor que cero'}.")
    return valor


def _coordenada(valor: object, *, campo: str, minimo: float, maximo: float) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DatosInvalidos(f"{campo} debe ser un número.")
    numero = float(valor)
    if not isfinite(numero) or not minimo <= numero <= maximo:
        raise DatosInvalidos(f"{campo} está fuera de rango.")
    return numero


def _validar_solicitud(solicitud: dict) -> tuple[str, float, float, list[tuple[str, int]]]:
    if not isinstance(solicitud, dict):
        raise DatosInvalidos("El pedido debe ser un objeto/diccionario.")
    cliente = solicitud.get("cliente")
    if not isinstance(cliente, str) or not 1 <= len(cliente.strip()) <= 120:
        raise DatosInvalidos("cliente es obligatorio (máximo 120 caracteres).")
    latitud = _coordenada(solicitud.get("latitud"), campo="latitud", minimo=-90, maximo=90)
    longitud = _coordenada(solicitud.get("longitud"), campo="longitud", minimo=-180, maximo=180)
    items = solicitud.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise DatosInvalidos("items debe contener entre 1 y 100 líneas.")

    agrupados: dict[str, int] = {}
    for numero_linea, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise DatosInvalidos(f"La línea {numero_linea} no es válida.")
        codigo = item.get("producto_codigo")
        if not isinstance(codigo, str) or not codigo.strip() or len(codigo) > 80:
            raise DatosInvalidos(f"La línea {numero_linea} requiere producto_codigo.")
        codigo = codigo.strip()
        cantidad = _entero_positivo(item.get("cantidad"), campo=f"cantidad de {codigo}")
        if cantidad > 10000:
            raise DatosInvalidos("No se permiten cantidades superiores a 10000 por línea.")
        agrupados[codigo] = agrupados.get(codigo, 0) + cantidad
        if agrupados[codigo] > 10000:
            raise DatosInvalidos(f"La cantidad acumulada de {codigo} supera 10000.")
    return cliente.strip(), latitud, longitud, sorted(agrupados.items())


def iniciar_modulo(db_path: str | Path = DEFAULT_DATABASE) -> None:
    """Agrega las tablas S2 a una base S1 existente; no altera su versión ni datos."""
    with connect_database(db_path) as db:
        db.executescript(SCRIPT.read_text(encoding="utf-8"))


def _revisar_modulo(db: sqlite3.Connection) -> None:
    tablas = {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 's2_%'"
    )}
    esperadas = {"s2_capacidades", "s2_pedidos", "s2_pedido_detalles", "s2_reservas"}
    if not esperadas.issubset(tablas):
        raise ModuloNoInicializado("Ejecuta primero: python -m src.backend.pedidos_s2_cli init")


def configurar_capacidad(
    sucursal_codigo: str, capacidad_maxima: int, db_path: str | Path = DEFAULT_DATABASE
) -> dict:
    """Configura pedidos activos máximos por sucursal (0 = deshabilitada)."""
    if not isinstance(sucursal_codigo, str) or not sucursal_codigo.strip():
        raise DatosInvalidos("Indica un código de sucursal válido.")
    _entero_positivo(capacidad_maxima, campo="capacidad_maxima", permitir_cero=True)
    with connect_database(db_path) as db:
        _revisar_modulo(db)
        db.execute("BEGIN IMMEDIATE")
        sucursal = db.execute("SELECT id, codigo FROM sucursales WHERE codigo = ?", (sucursal_codigo,)).fetchone()
        if sucursal is None:
            raise DatosInvalidos(f"La sucursal {sucursal_codigo} no existe.")
        db.execute("""
            INSERT INTO s2_capacidades(sucursal_id, capacidad_maxima) VALUES (?, ?)
            ON CONFLICT(sucursal_id) DO UPDATE SET capacidad_maxima = excluded.capacidad_maxima
        """, (sucursal["id"], capacidad_maxima))
    return {"sucursal": sucursal_codigo, "capacidad_maxima": capacidad_maxima}


def _productos_validos(db: sqlite3.Connection, items: list[tuple[str, int]]) -> list[dict]:
    codigos = [codigo for codigo, _ in items]
    placeholders = ",".join("?" for _ in codigos)
    encontrados = {r["codigo"]: dict(r) for r in db.execute(
        f"SELECT id, codigo, nombre FROM productos WHERE codigo IN ({placeholders})", codigos
    )}
    ausentes = [codigo for codigo in codigos if codigo not in encontrados]
    if ausentes:
        raise DatosInvalidos("Productos inexistentes: " + ", ".join(ausentes))
    return [{**encontrados[codigo], "cantidad": cantidad} for codigo, cantidad in items]


def _seleccionar_sucursal(db: sqlite3.Connection, lat: float, lon: float, productos: list[dict]) -> dict | None:
    # Stock y capacidad se comprueban mientras se retiene BEGIN IMMEDIATE.
    sucursales = db.execute("""
        SELECT s.id, s.codigo, s.nombre, s.latitud, s.longitud,
               c.capacidad_maxima,
               (SELECT count(*) FROM s2_pedidos AS p
                WHERE p.sucursal_id = s.id AND p.estado NOT IN ('ENTREGADO', 'CANCELADO')) AS ocupados
          FROM sucursales AS s
          JOIN s2_capacidades AS c ON c.sucursal_id = s.id
         WHERE c.capacidad_maxima > 0
    """).fetchall()
    candidatas: list[dict] = []
    for s in sucursales:
        libre = s["capacidad_maxima"] - s["ocupados"]
        if libre <= 0:
            continue
        inventario = {r["producto_id"]: r["cantidad"] for r in db.execute(
            "SELECT producto_id, cantidad FROM inventario WHERE sucursal_id = ?", (s["id"],)
        )}
        if any(inventario.get(p["id"], 0) < p["cantidad"] for p in productos):
            continue
        candidatas.append({
            "id": s["id"], "codigo": s["codigo"], "nombre": s["nombre"],
            "capacidad_libre": libre,
            "distancia_km": distancia_km(lat, lon, s["latitud"], s["longitud"]),
        })
    return ordenar_candidatas(candidatas)[0] if candidatas else None


def registrar_pedido(solicitud: dict, db_path: str | Path = DEFAULT_DATABASE) -> dict:
    """Valida, persiste, asigna y reserva de manera atómica.

    Si no existe sucursal elegible, persiste un pedido SIN_ASIGNAR, sin reservas.
    No reduce stock hasta comprobar todos los productos y la capacidad de la tienda.
    BEGIN IMMEDIATE serializa escritores concurrentes y evita sobreventa.
    """
    cliente, lat, lon, items = _validar_solicitud(solicitud)
    with connect_database(db_path) as db:
        _revisar_modulo(db)
        db.execute("BEGIN IMMEDIATE")
        productos = _productos_validos(db, items)
        sucursal = _seleccionar_sucursal(db, lat, lon, productos)
        estado = "ASIGNADO" if sucursal else "SIN_ASIGNAR"
        motivo = None if sucursal else "Ninguna sucursal tiene stock suficiente y capacidad libre."
        cursor = db.execute("""
            INSERT INTO s2_pedidos(cliente, latitud, longitud, sucursal_id, estado, distancia_km,
                                   motivo_sin_asignar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, lat, lon, sucursal["id"] if sucursal else None, estado,
              sucursal["distancia_km"] if sucursal else None, motivo))
        pedido_id = cursor.lastrowid
        for producto in productos:
            detalle = db.execute("""
                INSERT INTO s2_pedido_detalles(pedido_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            """, (pedido_id, producto["id"], producto["cantidad"]))
            if sucursal:
                actualizado = db.execute("""
                    UPDATE inventario SET cantidad = cantidad - ?
                     WHERE producto_id = ? AND sucursal_id = ? AND cantidad >= ?
                """, (producto["cantidad"], producto["id"], sucursal["id"], producto["cantidad"]))
                if actualizado.rowcount != 1:
                    # Revierte el pedido y todas las reservas si el inventario falla.
                    raise RuntimeError("El inventario cambió durante la asignación; no se guardó el pedido.")
                db.execute("""
                    INSERT INTO s2_reservas(detalle_id, sucursal_id, cantidad) VALUES (?, ?, ?)
                """, (detalle.lastrowid, sucursal["id"], producto["cantidad"]))
        return {
            "pedido_id": pedido_id,
            "estado": estado,
            "sucursal_codigo": sucursal["codigo"] if sucursal else None,
            "sucursal_nombre": sucursal["nombre"] if sucursal else None,
            "distancia_km": round(sucursal["distancia_km"], 3) if sucursal else None,
            "motivo": motivo,
            "items": [{"producto_codigo": p["codigo"], "cantidad": p["cantidad"]} for p in productos],
        }


def obtener_pedido(pedido_id: int, db_path: str | Path = DEFAULT_DATABASE) -> dict | None:
    """Recupera el pedido persistido y los detalles, sin modificar inventario."""
    _entero_positivo(pedido_id, campo="pedido_id")
    with connect_database(db_path, read_only=True) as db:
        _revisar_modulo(db)
        pedido = db.execute("""
            SELECT p.id, p.cliente, p.latitud, p.longitud, p.estado, p.creado_en,
                   p.distancia_km, p.motivo_sin_asignar,
                   s.codigo AS sucursal_codigo, s.nombre AS sucursal_nombre
              FROM s2_pedidos p LEFT JOIN sucursales s ON s.id = p.sucursal_id
             WHERE p.id = ?
        """, (pedido_id,)).fetchone()
        if pedido is None:
            return None
        detalles = db.execute("""
            SELECT prod.codigo AS producto_codigo, d.cantidad,
                   CASE WHEN r.id IS NULL THEN 0 ELSE 1 END AS reservada
              FROM s2_pedido_detalles d
              JOIN productos prod ON prod.id = d.producto_id
              LEFT JOIN s2_reservas r ON r.detalle_id = d.id
             WHERE d.pedido_id = ? ORDER BY prod.codigo
        """, (pedido_id,)).fetchall()
        resultado = dict(pedido)
        resultado["items"] = [dict(x) for x in detalles]
        return resultado
