"""S3-04 / Issue #22: transiciones de reparto y soporte de pedidos.

En este módulo valido quién puede cambiar el estado de un pedido, sincronizo
el estado de la entrega y registro incidencias sin reemplazar los servicios
de preparación ni las funciones de fechas del Sprint 3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.database.database import DEFAULT_DATABASE, connect_database

ROLES = {
    "PERSONAL_SUCURSAL",
    "REPARTIDOR",
    "ASESOR",
    "ADMINISTRADOR",
}

CATEGORIAS_INCIDENCIA = {
    "RETRASO",
    "PRODUCTO_FALTANTE",
    "PRODUCTO_DANADO",
    "DIRECCION_INCORRECTA",
    "CLIENTE_AUSENTE",
    "OTRO",
}

ESTADOS_INCIDENCIA = {"ABIERTA", "EN_REVISION", "RESUELTA"}


class ErrorSoportePedido(ValueError):
    """Error base de validación del módulo de soporte."""


class PedidoNoEncontrado(ErrorSoportePedido):
    """El pedido solicitado no existe."""


class IncidenciaNoEncontrada(ErrorSoportePedido):
    """La incidencia solicitada no existe o no está disponible para el rol."""


class PermisoDenegado(ErrorSoportePedido):
    """El rol indicado no puede realizar la operación."""


class TransicionPedidoInvalida(ErrorSoportePedido):
    """El pedido no puede pasar al estado solicitado."""


class TransicionIncidenciaInvalida(ErrorSoportePedido):
    """La incidencia no puede pasar al estado solicitado."""


class DatosIncidenciaInvalidos(ErrorSoportePedido):
    """La categoría o descripción de la incidencia no es válida."""


def _validar_id(valor, campo: str, *, obligatorio: bool = True):
    if valor is None and not obligatorio:
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ErrorSoportePedido(f"{campo} debe ser un entero positivo.")
    return valor


def _validar_rol(rol: str) -> str:
    if not isinstance(rol, str):
        raise PermisoDenegado("Debes indicar un rol válido.")
    normalizado = rol.strip().upper()
    if normalizado not in ROLES:
        raise PermisoDenegado(
            "Rol no reconocido. Usa PERSONAL_SUCURSAL, REPARTIDOR, ASESOR o ADMINISTRADOR."
        )
    return normalizado


def _validar_texto(valor, campo: str, maximo: int, minimo: int = 1) -> str:
    if not isinstance(valor, str):
        raise ErrorSoportePedido(f"{campo} debe ser texto.")
    limpio = valor.strip()
    if not minimo <= len(limpio) <= maximo:
        raise ErrorSoportePedido(
            f"{campo} debe tener entre {minimo} y {maximo} caracteres."
        )
    return limpio


def _verificar_esquema_soporte(db: sqlite3.Connection) -> None:
    version = db.execute("PRAGMA user_version").fetchone()[0]
    existe = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='incidencias_pedido'"
    ).fetchone()
    if version < 4 or existe is None:
        raise ErrorSoportePedido(
            "Falta aplicar la migración S3-04. Ejecuta: "
            "python -m src.database.migrate_josue --hasta 4"
        )


def _pedido(db: sqlite3.Connection, pedido_id: int):
    fila = db.execute(
        """
        SELECT p.id, p.codigo, p.sucursal_id, p.estado,
               s.codigo AS sucursal_codigo
          FROM pedidos p
          JOIN sucursales s ON s.id = p.sucursal_id
         WHERE p.id = ?
        """,
        (pedido_id,),
    ).fetchone()
    if fila is None:
        raise PedidoNoEncontrado(f"No existe el pedido con ID {pedido_id}.")
    return fila


def _incidencia(db: sqlite3.Connection, incidencia_id: int) -> dict:
    fila = db.execute(
        """
        SELECT i.id, i.pedido_id, p.codigo AS pedido_codigo,
               p.estado AS estado_pedido, s.codigo AS sucursal_codigo,
               i.categoria, i.descripcion, i.reportado_por_rol,
               i.reportado_por_id, i.estado, i.resolucion,
               i.atendido_por_rol, i.atendido_por_id,
               i.fecha_creacion, i.fecha_actualizacion, i.fecha_resolucion
          FROM incidencias_pedido i
          JOIN pedidos p ON p.id = i.pedido_id
          JOIN sucursales s ON s.id = p.sucursal_id
         WHERE i.id = ?
        """,
        (incidencia_id,),
    ).fetchone()
    return dict(fila) if fila else None


def _validar_reportante(
    db: sqlite3.Connection,
    pedido,
    rol: str,
    actor_id: int | None,
) -> int | None:
    """Compruebo que el reportante pertenezca a la sucursal o entrega indicada."""
    if rol == "PERSONAL_SUCURSAL":
        _validar_id(actor_id, "actor_id")
        if actor_id != pedido["sucursal_id"]:
            raise PermisoDenegado(
                "El personal solo puede reportar incidencias de su propia sucursal."
            )
    elif rol == "REPARTIDOR":
        _validar_id(actor_id, "actor_id")
        entrega = db.execute(
            "SELECT repartidor_id FROM entregas WHERE pedido_id = ?",
            (pedido["id"],),
        ).fetchone()
        if entrega is None or entrega["repartidor_id"] != actor_id:
            raise PermisoDenegado(
                "El repartidor solo puede reportar incidencias de sus entregas asignadas."
            )
    elif actor_id is not None:
        _validar_id(actor_id, "actor_id")
    return actor_id


def cambiar_estado_pedido(
    pedido_id: int,
    nuevo_estado: str,
    rol: str,
    actor_id: int | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Valido y sincronizo las dos transiciones de reparto del pedido.

    PREPARADO -> EN_CAMINO requiere la fecha de salida registrada.
    EN_CAMINO -> ENTREGADO requiere la fecha de recepción registrada.
    En ambas etapas solo puede actuar el repartidor asignado a la entrega.
    """
    _validar_id(pedido_id, "pedido_id")
    _validar_id(actor_id, "actor_id")
    rol = _validar_rol(rol)
    if rol != "REPARTIDOR":
        raise PermisoDenegado(
            "Solo el repartidor asignado puede iniciar o confirmar el reparto."
        )
    if not isinstance(nuevo_estado, str):
        raise TransicionPedidoInvalida("El estado destino debe ser texto.")
    nuevo_estado = nuevo_estado.strip().upper()
    if nuevo_estado not in {"EN_CAMINO", "ENTREGADO"}:
        raise TransicionPedidoInvalida(
            "Desde este módulo solo gestiono EN_CAMINO y ENTREGADO."
        )

    with connect_database(db_path) as db:
        _verificar_esquema_soporte(db)
        db.execute("BEGIN IMMEDIATE")
        pedido = _pedido(db, pedido_id)
        entrega = db.execute(
            """
            SELECT id, repartidor_id, estado, fecha_salida, fecha_entrega
              FROM entregas
             WHERE pedido_id = ?
            """,
            (pedido_id,),
        ).fetchone()

        if entrega is None:
            raise TransicionPedidoInvalida(
                "El pedido todavía no tiene una entrega asignada."
            )
        if entrega["repartidor_id"] != actor_id:
            raise PermisoDenegado(
                "Solo el repartidor asignado a este pedido puede cambiar su estado."
            )

        if pedido["estado"] == "PREPARADO" and nuevo_estado == "EN_CAMINO":
            if entrega["estado"] != "ASIGNADA" or not entrega["fecha_salida"]:
                raise TransicionPedidoInvalida(
                    "Primero debo registrar la fecha de salida de la entrega."
                )
            estado_entrega = "EN_CAMINO"
            # Cuando el pedido sale de la sucursal, consumo las reservas activas.
            # El trigger de la migración 002 descuenta el inventario una sola vez.
            reservas_consumidas = db.execute(
                """
                UPDATE reservas_stock
                   SET estado = 'CONSUMIDA',
                       fecha_cierre = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                 WHERE pedido_id = ? AND estado = 'ACTIVA'
                """,
                (pedido_id,),
            ).rowcount
        elif pedido["estado"] == "EN_CAMINO" and nuevo_estado == "ENTREGADO":
            if (
                entrega["estado"] != "EN_CAMINO"
                or not entrega["fecha_salida"]
                or not entrega["fecha_entrega"]
            ):
                raise TransicionPedidoInvalida(
                    "Primero debo registrar la salida y la recepción del pedido."
                )
            estado_entrega = "ENTREGADA"
            reservas_consumidas = 0
        else:
            raise TransicionPedidoInvalida(
                f"No permito cambiar el pedido de {pedido['estado']} a {nuevo_estado}."
            )

        db.execute(
            "UPDATE pedidos SET estado = ? WHERE id = ?",
            (nuevo_estado, pedido_id),
        )
        db.execute(
            "UPDATE entregas SET estado = ? WHERE id = ?",
            (estado_entrega, entrega["id"]),
        )
        return {
            "pedido_id": pedido_id,
            "pedido_codigo": pedido["codigo"],
            "estado_anterior": pedido["estado"],
            "estado_nuevo": nuevo_estado,
            "estado_entrega": estado_entrega,
            "repartidor_id": actor_id,
            "reservas_consumidas": reservas_consumidas,
        }


def cancelar_pedido(
    pedido_id: int,
    rol: str,
    actor_id: int | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Permito al administrador cancelar antes de que el repartidor salga.

    Al cancelar libero las reservas activas dentro de la misma transacción.
    """
    _validar_id(pedido_id, "pedido_id")
    if actor_id is not None:
        _validar_id(actor_id, "actor_id")
    rol = _validar_rol(rol)
    if rol != "ADMINISTRADOR":
        raise PermisoDenegado("Solo el administrador puede cancelar un pedido.")

    with connect_database(db_path) as db:
        _verificar_esquema_soporte(db)
        db.execute("BEGIN IMMEDIATE")
        pedido = _pedido(db, pedido_id)
        if pedido["estado"] not in {
            "REGISTRADO", "ASIGNADO", "EN_PREPARACION", "PREPARADO"
        }:
            raise TransicionPedidoInvalida(
                f"No puedo cancelar un pedido que está en estado {pedido['estado']}."
            )

        entrega = db.execute(
            "SELECT id, estado, fecha_salida FROM entregas WHERE pedido_id = ?",
            (pedido_id,),
        ).fetchone()
        if entrega is not None and (
            entrega["estado"] in {"EN_CAMINO", "ENTREGADA"}
            or entrega["fecha_salida"] is not None
        ):
            raise TransicionPedidoInvalida(
                "No puedo cancelar el pedido después de registrar la salida del repartidor."
            )

        reservas = db.execute(
            """
            UPDATE reservas_stock
               SET estado = 'LIBERADA',
                   fecha_cierre = strftime('%Y-%m-%dT%H:%M:%fZ','now')
             WHERE pedido_id = ? AND estado = 'ACTIVA'
            """,
            (pedido_id,),
        ).rowcount

        if entrega is not None and entrega["estado"] == "ASIGNADA":
            db.execute(
                """
                UPDATE entregas
                   SET estado = 'FALLIDA',
                       observaciones = CASE
                           WHEN observaciones IS NULL OR trim(observaciones) = ''
                           THEN 'Pedido cancelado por administración antes de la salida.'
                           ELSE observaciones || ' | Pedido cancelado por administración antes de la salida.'
                       END
                 WHERE id = ?
                """,
                (entrega["id"],),
            )

        db.execute(
            "UPDATE pedidos SET estado = 'CANCELADO' WHERE id = ?",
            (pedido_id,),
        )
        return {
            "pedido_id": pedido_id,
            "estado_anterior": pedido["estado"],
            "estado_nuevo": "CANCELADO",
            "reservas_liberadas": reservas,
        }


def registrar_incidencia(
    pedido_id: int,
    categoria: str,
    descripcion: str,
    rol: str,
    actor_id: int | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Registro un problema y lo relaciono con el pedido correspondiente."""
    _validar_id(pedido_id, "pedido_id")
    rol = _validar_rol(rol)
    if not isinstance(categoria, str):
        raise DatosIncidenciaInvalidos("La categoría debe ser texto.")
    categoria = categoria.strip().upper()
    if categoria not in CATEGORIAS_INCIDENCIA:
        raise DatosIncidenciaInvalidos(
            "Categoría no válida. Usa: " + ", ".join(sorted(CATEGORIAS_INCIDENCIA))
        )
    descripcion = _validar_texto(descripcion, "descripcion", 2000, 5)

    with connect_database(db_path) as db:
        _verificar_esquema_soporte(db)
        db.execute("BEGIN IMMEDIATE")
        pedido = _pedido(db, pedido_id)
        actor_id = _validar_reportante(db, pedido, rol, actor_id)
        cursor = db.execute(
            """
            INSERT INTO incidencias_pedido (
                pedido_id, categoria, descripcion,
                reportado_por_rol, reportado_por_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (pedido_id, categoria, descripcion, rol, actor_id),
        )
        return _incidencia(db, cursor.lastrowid)


def listar_incidencias(
    rol: str,
    actor_id: int | None = None,
    estado: str | None = None,
    pedido_id: int | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> list[dict]:
    """Consulto incidencias según el alcance del rol que realiza la consulta."""
    rol = _validar_rol(rol)
    if actor_id is not None:
        _validar_id(actor_id, "actor_id")
    if pedido_id is not None:
        _validar_id(pedido_id, "pedido_id")
    if estado is not None:
        if not isinstance(estado, str) or estado.strip().upper() not in ESTADOS_INCIDENCIA:
            raise DatosIncidenciaInvalidos("El estado de incidencia no es válido.")
        estado = estado.strip().upper()

    condiciones = []
    parametros = []
    if estado:
        condiciones.append("i.estado = ?")
        parametros.append(estado)
    if pedido_id is not None:
        condiciones.append("i.pedido_id = ?")
        parametros.append(pedido_id)

    if rol == "PERSONAL_SUCURSAL":
        _validar_id(actor_id, "actor_id")
        condiciones.append("p.sucursal_id = ?")
        parametros.append(actor_id)
    elif rol == "REPARTIDOR":
        _validar_id(actor_id, "actor_id")
        condiciones.append(
            "EXISTS (SELECT 1 FROM entregas e WHERE e.pedido_id = p.id AND e.repartidor_id = ?)"
        )
        parametros.append(actor_id)
    elif rol not in {"ASESOR", "ADMINISTRADOR"}:
        raise PermisoDenegado("No tienes permiso para consultar incidencias.")

    consulta = """
        SELECT i.id, i.pedido_id, p.codigo AS pedido_codigo,
               p.estado AS estado_pedido, s.codigo AS sucursal_codigo,
               i.categoria, i.descripcion, i.reportado_por_rol,
               i.reportado_por_id, i.estado, i.resolucion,
               i.atendido_por_rol, i.atendido_por_id,
               i.fecha_creacion, i.fecha_actualizacion, i.fecha_resolucion
          FROM incidencias_pedido i
          JOIN pedidos p ON p.id = i.pedido_id
          JOIN sucursales s ON s.id = p.sucursal_id
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY i.fecha_creacion DESC, i.id DESC"

    with connect_database(db_path, read_only=True) as db:
        _verificar_esquema_soporte(db)
        filas = db.execute(consulta, parametros).fetchall()
        return [dict(fila) for fila in filas]


def obtener_incidencia(
    incidencia_id: int,
    rol: str,
    actor_id: int | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Consulto una incidencia aplicando los mismos permisos de la bandeja."""
    _validar_id(incidencia_id, "incidencia_id")
    with connect_database(db_path, read_only=True) as db:
        _verificar_esquema_soporte(db)
        existe = db.execute(
            "SELECT pedido_id FROM incidencias_pedido WHERE id = ?",
            (incidencia_id,),
        ).fetchone()
        if existe is None:
            raise IncidenciaNoEncontrada(
                f"No existe la incidencia con ID {incidencia_id}."
            )
    resultados = listar_incidencias(
        rol=rol, actor_id=actor_id, pedido_id=existe["pedido_id"], db_path=db_path
    )
    for incidencia in resultados:
        if incidencia["id"] == incidencia_id:
            return incidencia
    raise IncidenciaNoEncontrada(
        "La incidencia no existe o no tienes permiso para consultarla."
    )


def actualizar_estado_incidencia(
    incidencia_id: int,
    nuevo_estado: str,
    rol: str,
    actor_id: int | None = None,
    resolucion: str | None = None,
    db_path: str | Path = DEFAULT_DATABASE,
) -> dict:
    """Atiendo una incidencia: ABIERTA -> EN_REVISION -> RESUELTA."""
    _validar_id(incidencia_id, "incidencia_id")
    if actor_id is not None:
        _validar_id(actor_id, "actor_id")
    rol = _validar_rol(rol)
    if rol not in {"ASESOR", "ADMINISTRADOR"}:
        raise PermisoDenegado(
            "Solo un asesor o administrador puede gestionar incidencias."
        )
    if not isinstance(nuevo_estado, str):
        raise TransicionIncidenciaInvalida("El estado destino debe ser texto.")
    nuevo_estado = nuevo_estado.strip().upper()
    if nuevo_estado not in {"EN_REVISION", "RESUELTA"}:
        raise TransicionIncidenciaInvalida(
            "Solo puedo pasar una incidencia a EN_REVISION o RESUELTA."
        )

    texto_resolucion = None
    if nuevo_estado == "RESUELTA":
        texto_resolucion = _validar_texto(
            resolucion, "resolucion", 2000, 5
        )
    elif resolucion is not None:
        raise TransicionIncidenciaInvalida(
            "Solo registro una resolución cuando cierro la incidencia."
        )

    with connect_database(db_path) as db:
        _verificar_esquema_soporte(db)
        db.execute("BEGIN IMMEDIATE")
        actual = db.execute(
            "SELECT id, estado FROM incidencias_pedido WHERE id = ?",
            (incidencia_id,),
        ).fetchone()
        if actual is None:
            raise IncidenciaNoEncontrada(
                f"No existe la incidencia con ID {incidencia_id}."
            )

        if actual["estado"] == "ABIERTA" and nuevo_estado == "EN_REVISION":
            db.execute(
                """
                UPDATE incidencias_pedido
                   SET estado = 'EN_REVISION',
                       atendido_por_rol = ?,
                       atendido_por_id = ?,
                       fecha_actualizacion = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                 WHERE id = ?
                """,
                (rol, actor_id, incidencia_id),
            )
        elif actual["estado"] == "EN_REVISION" and nuevo_estado == "RESUELTA":
            db.execute(
                """
                UPDATE incidencias_pedido
                   SET estado = 'RESUELTA',
                       resolucion = ?,
                       atendido_por_rol = ?,
                       atendido_por_id = ?,
                       fecha_actualizacion = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
                       fecha_resolucion = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                 WHERE id = ?
                """,
                (texto_resolucion, rol, actor_id, incidencia_id),
            )
        else:
            raise TransicionIncidenciaInvalida(
                f"No permito pasar la incidencia de {actual['estado']} a {nuevo_estado}."
            )
        return _incidencia(db, incidencia_id)


def obtener_historial_pedido(
    pedido_id: int,
    db_path: str | Path = DEFAULT_DATABASE,
) -> list[dict]:
    """Consulto el historial de estados que la migración v3 guarda automáticamente."""
    _validar_id(pedido_id, "pedido_id")
    with connect_database(db_path, read_only=True) as db:
        _verificar_esquema_soporte(db)
        if db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is None:
            raise PedidoNoEncontrado(f"No existe el pedido con ID {pedido_id}.")
        filas = db.execute(
            """
            SELECT id, pedido_id, estado_anterior, estado_nuevo,
                   fecha_cambio, observacion
              FROM historial_estados
             WHERE pedido_id = ?
             ORDER BY id
            """,
            (pedido_id,),
        ).fetchall()
        return [dict(fila) for fila in filas]
