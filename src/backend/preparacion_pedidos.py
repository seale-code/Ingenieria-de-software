"""Gestion de preparacion de pedidos en sucursal (S3-01 / Issue #16).

Permite consultar los pedidos asignados a una sucursal y registrar el avance
de su preparacion mediante transiciones de estado validas:
    REGISTRADO / ASIGNADO -> EN_PREPARACION -> PREPARADO
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.database import DEFAULT_DATABASE, connect_database

ESTADOS_GESTION_PREPARACION = ("REGISTRADO", "ASIGNADO", "EN_PREPARACION", "PREPARADO")

TRANSICIONES_PREPARACION_PERMITIDAS: dict[str, tuple[str, ...]] = {
    "REGISTRADO": ("EN_PREPARACION",),
    "ASIGNADO": ("EN_PREPARACION",),
    "EN_PREPARACION": ("PREPARADO",),
    "PREPARADO": (),
    "EN_CAMINO": (),
    "ENTREGADO": (),
    "CANCELADO": (),
}


class ErrorPreparacionPedido(ValueError):
    """Error base para operaciones invalidas durante la preparacion de pedidos."""


class PedidoNoEncontrado(ErrorPreparacionPedido):
    """El pedido indicado no existe en la base de datos."""


class TransicionPreparacionInvalida(ErrorPreparacionPedido):
    """La transicion de estado solicitada no esta permitida en preparacion."""


def validar_transicion_preparacion(estado_actual: str, nuevo_estado: str) -> None:
    """Verifica que el cambio de estado sea una transicion valida de preparacion."""
    if not isinstance(nuevo_estado, str) or nuevo_estado.strip() not in (
        "EN_PREPARACION",
        "PREPARADO",
    ):
        raise TransicionPreparacionInvalida(
            f"El estado destino '{nuevo_estado}' no corresponde a una etapa de preparacion "
            "('EN_PREPARACION' o 'PREPARADO')."
        )

    destino = nuevo_estado.strip()
    permitidos = TRANSICIONES_PREPARACION_PERMITIDAS.get(estado_actual, ())
    if destino not in permitidos:
        raise TransicionPreparacionInvalida(
            f"Transicion invalida: no se puede pasar un pedido de '{estado_actual}' a '{destino}'."
        )


def _tiene_tabla(db: sqlite3.Connection, nombre_tabla: str) -> bool:
    fila = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (nombre_tabla,),
    ).fetchone()
    return fila is not None


def _obtener_items_pedido(db: sqlite3.Connection, pedido_id: int) -> list[dict]:
    filas = db.execute(
        """
        SELECT d.producto_id,
               p.codigo AS producto_codigo,
               p.nombre AS producto_nombre,
               d.cantidad,
               r.estado AS estado_reserva
          FROM detalles_pedido AS d
          JOIN productos AS p ON p.id = d.producto_id
          LEFT JOIN reservas_stock AS r
            ON r.pedido_id = d.pedido_id AND r.producto_id = d.producto_id
         WHERE d.pedido_id = ?
         ORDER BY p.codigo
        """,
        (pedido_id,),
    ).fetchall()
    return [dict(f) for f in filas]


def _obtener_historial_pedido(db: sqlite3.Connection, pedido_id: int) -> list[dict]:
    if not _tiene_tabla(db, "historial_estados"):
        return []
    filas = db.execute(
        """
        SELECT id, estado_anterior, estado_nuevo, fecha_cambio, observacion
          FROM historial_estados
         WHERE pedido_id = ?
         ORDER BY id ASC
        """,
        (pedido_id,),
    ).fetchall()
    return [dict(f) for f in filas]


def obtener_pedido_preparacion(
    pedido_id: int,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Obtiene el detalle completo de un pedido para su gestion de preparacion."""
    if isinstance(pedido_id, bool) or not isinstance(pedido_id, int) or pedido_id <= 0:
        raise ErrorPreparacionPedido("El identificador del pedido debe ser un entero positivo.")

    with connect_database(db_path, read_only=True) as db:
        return _consultar_pedido_por_id(db, pedido_id)


def _consultar_pedido_por_id(db: sqlite3.Connection, pedido_id: int) -> dict:
    tiene_solicitudes = _tiene_tabla(db, "s2_solicitudes")
    if tiene_solicitudes:
        consulta = """
            SELECT p.id AS pedido_id,
                   p.codigo AS pedido_codigo,
                   p.estado,
                   p.fecha_creacion,
                   s.codigo AS sucursal_codigo,
                   s.nombre AS sucursal_nombre,
                   sol.cliente
              FROM pedidos AS p
              JOIN sucursales AS s ON s.id = p.sucursal_id
              LEFT JOIN s2_solicitudes AS sol ON sol.pedido_id = p.id
             WHERE p.id = ?
        """
    else:
        consulta = """
            SELECT p.id AS pedido_id,
                   p.codigo AS pedido_codigo,
                   p.estado,
                   p.fecha_creacion,
                   s.codigo AS sucursal_codigo,
                   s.nombre AS sucursal_nombre,
                   NULL AS cliente
              FROM pedidos AS p
              JOIN sucursales AS s ON s.id = p.sucursal_id
             WHERE p.id = ?
        """

    fila = db.execute(consulta, (pedido_id,)).fetchone()
    if fila is None:
        raise PedidoNoEncontrado(f"No existe el pedido con id {pedido_id}.")

    pedido = dict(fila)
    pedido["items"] = _obtener_items_pedido(db, pedido_id)
    pedido["historial"] = _obtener_historial_pedido(db, pedido_id)
    return pedido


def consultar_pedidos_asignados(
    sucursal_codigo: str | None = None,
    estado: str | None = None,
    incluir_preparados: bool = True,
    db_path: str | Path = DEFAULT_DATABASE,
) -> list[dict]:
    """Consulta los pedidos asignados para preparacion, filtrando por sucursal y estado."""
    if sucursal_codigo is not None and not isinstance(sucursal_codigo, str):
        raise ErrorPreparacionPedido("El codigo de sucursal debe ser texto o None.")
    if estado is not None and not isinstance(estado, str):
        raise ErrorPreparacionPedido("El estado de filtro debe ser texto o None.")

    sucursal_limpia = sucursal_codigo.strip() if isinstance(sucursal_codigo, str) and sucursal_codigo.strip() else None
    estado_limpio = estado.strip() if isinstance(estado, str) and estado.strip() else None

    if estado_limpio is not None and estado_limpio not in ESTADOS_GESTION_PREPARACION:
        raise ErrorPreparacionPedido(
            f"El estado '{estado_limpio}' no pertenece a la bandeja de preparacion."
        )

    condiciones: list[str] = []
    parametros: list[object] = []

    if estado_limpio:
        condiciones.append("p.estado = ?")
        parametros.append(estado_limpio)
    else:
        estados_bandeja = (
            ("REGISTRADO", "ASIGNADO", "EN_PREPARACION", "PREPARADO")
            if incluir_preparados
            else ("REGISTRADO", "ASIGNADO", "EN_PREPARACION")
        )
        placeholders = ", ".join("?" for _ in estados_bandeja)
        condiciones.append(f"p.estado IN ({placeholders})")
        parametros.extend(estados_bandeja)

    if sucursal_limpia:
        condiciones.append("s.codigo = ?")
        parametros.append(sucursal_limpia)

    where_sql = " AND ".join(condiciones)

    with connect_database(db_path, read_only=True) as db:
        ids = db.execute(
            f"""
            SELECT p.id
              FROM pedidos AS p
              JOIN sucursales AS s ON s.id = p.sucursal_id
             WHERE {where_sql}
             ORDER BY p.id ASC
            """,
            parametros,
        ).fetchall()

        return [_consultar_pedido_por_id(db, fila["id"]) for fila in ids]


def registrar_avance_preparacion(
    pedido_id: int,
    nuevo_estado: str,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Actualiza el estado de preparacion del pedido aplicando validacion de transiciones."""
    if isinstance(pedido_id, bool) or not isinstance(pedido_id, int) or pedido_id <= 0:
        raise ErrorPreparacionPedido("El identificador del pedido debe ser un entero positivo.")

    with connect_database(db_path) as db:
        db.execute("BEGIN IMMEDIATE")
        actual = db.execute(
            "SELECT id, estado FROM pedidos WHERE id = ?",
            (pedido_id,),
        ).fetchone()
        if actual is None:
            raise PedidoNoEncontrado(f"No existe el pedido con id {pedido_id}.")

        estado_anterior = actual["estado"]
        validar_transicion_preparacion(estado_anterior, nuevo_estado)
        destino = nuevo_estado.strip()

        detalles = db.execute(
            "SELECT count(*) FROM detalles_pedido WHERE pedido_id = ?",
            (pedido_id,),
        ).fetchone()[0]
        if detalles == 0:
            raise ErrorPreparacionPedido(
                "No se puede preparar un pedido que no tiene productos en su detalle."
            )

        db.execute(
            "UPDATE pedidos SET estado = ? WHERE id = ?",
            (destino, pedido_id),
        )

        pedido_actualizado = _consultar_pedido_por_id(db, pedido_id)
        return {
            "pedido_id": pedido_id,
            "estado_anterior": estado_anterior,
            "estado_nuevo": destino,
            "pedido": pedido_actualizado,
        }


def iniciar_preparacion_pedido(
    pedido_id: int,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Pasa un pedido asignado al estado EN_PREPARACION."""
    return registrar_avance_preparacion(
        pedido_id=pedido_id,
        nuevo_estado="EN_PREPARACION",
        db_path=db_path,
    )


def completar_preparacion_pedido(
    pedido_id: int,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Pasa un pedido en preparacion al estado PREPARADO."""
    return registrar_avance_preparacion(
        pedido_id=pedido_id,
        nuevo_estado="PREPARADO",
        db_path=db_path,
    )
