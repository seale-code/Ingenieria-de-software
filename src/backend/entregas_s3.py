"""S3-03: registro y consulta de entregas de Inkafarma."""

import sqlite3

from src.database.database import DEFAULT_DATABASE, connect_database


class DatosEntregaInvalidos(ValueError):
    """Los datos de la entrega no son válidos."""


class PedidoNoEncontrado(LookupError):
    """El pedido indicado no existe."""


class RepartidorNoDisponible(LookupError):
    """El repartidor no existe o está inactivo."""


class EntregaDuplicada(ValueError):
    """El pedido ya tiene una entrega registrada."""


ESTADOS_ENTREGA = {
    "ASIGNADA",
    "EN_CAMINO",
    "ENTREGADA",
    "FALLIDA",
}


def _validar_id(valor, campo):
    if (
        isinstance(valor, bool)
        or not isinstance(valor, int)
        or valor <= 0
    ):
        raise DatosEntregaInvalidos(
            f"{campo} debe ser un entero positivo."
        )


def _validar_observaciones(valor):
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise DatosEntregaInvalidos(
            "Las observaciones deben ser texto."
        )

    valor = valor.strip()

    if len(valor) > 1000:
        raise DatosEntregaInvalidos(
            "Las observaciones no pueden superar 1000 caracteres."
        )

    return valor or None


def _obtener_entrega_db(db, entrega_id):
    fila = db.execute(
        """
        SELECT
            e.id,
            e.pedido_id,
            p.codigo AS pedido_codigo,
            p.estado AS estado_pedido,
            e.repartidor_id,
            r.codigo AS repartidor_codigo,
            r.nombre AS repartidor_nombre,
            e.estado AS estado_entrega,
            e.fecha_asignacion,
            e.fecha_salida,
            e.fecha_entrega,
            e.observaciones
        FROM entregas e
        JOIN pedidos p ON p.id = e.pedido_id
        JOIN repartidores r ON r.id = e.repartidor_id
        WHERE e.id = ?
        """,
        (entrega_id,)
    ).fetchone()

    return dict(fila) if fila else None


def registrar_entrega(
    pedido_id,
    repartidor_id,
    observaciones=None,
    db_path=DEFAULT_DATABASE
):
    """Registra una entrega y la relaciona con pedido y repartidor."""

    _validar_id(pedido_id, "pedido_id")
    _validar_id(repartidor_id, "repartidor_id")

    observaciones = _validar_observaciones(observaciones)

    try:
        with connect_database(db_path) as db:

            db.execute("BEGIN IMMEDIATE")

            pedido = db.execute(
                """
                SELECT id, estado
                FROM pedidos
                WHERE id = ?
                """,
                (pedido_id,)
            ).fetchone()

            if pedido is None:
                raise PedidoNoEncontrado(
                    "El pedido indicado no existe."
                )

            if pedido["estado"] in ("ENTREGADO", "CANCELADO"):
                raise DatosEntregaInvalidos(
                    "No se puede asignar una entrega a un pedido cerrado."
                )

            repartidor = db.execute(
                """
                SELECT id, activo
                FROM repartidores
                WHERE id = ?
                """,
                (repartidor_id,)
            ).fetchone()

            if repartidor is None or repartidor["activo"] != 1:
                raise RepartidorNoDisponible(
                    "El repartidor no existe o está inactivo."
                )

            existente = db.execute(
                """
                SELECT id
                FROM entregas
                WHERE pedido_id = ?
                """,
                (pedido_id,)
            ).fetchone()

            if existente:
                raise EntregaDuplicada(
                    "El pedido ya tiene una entrega registrada."
                )

            cursor = db.execute(
                """
                INSERT INTO entregas (
                    pedido_id,
                    repartidor_id,
                    observaciones
                )
                VALUES (?, ?, ?)
                """,
                (pedido_id, repartidor_id, observaciones)
            )

            return _obtener_entrega_db(
                db,
                cursor.lastrowid
            )

    except sqlite3.IntegrityError as error:
        if "UNIQUE" in str(error).upper():
            raise EntregaDuplicada(
                "El pedido ya tiene una entrega registrada."
            ) from None

        raise


def obtener_entrega(
    entrega_id,
    db_path=DEFAULT_DATABASE
):
    """Consulta una entrega por su identificador."""

    _validar_id(entrega_id, "entrega_id")

    with connect_database(db_path, read_only=True) as db:
        return _obtener_entrega_db(db, entrega_id)


def listar_entregas(
    estado=None,
    repartidor_id=None,
    db_path=DEFAULT_DATABASE
):
    """Lista entregas con filtros opcionales."""

    if estado is not None:
        if not isinstance(estado, str) or estado not in ESTADOS_ENTREGA:
            raise DatosEntregaInvalidos(
                "El estado de entrega no es válido."
            )

    condiciones = []
    parametros = []

    if estado is not None:
        condiciones.append("e.estado = ?")
        parametros.append(estado)

    if repartidor_id is not None:
        _validar_id(repartidor_id, "repartidor_id")
        condiciones.append("e.repartidor_id = ?")
        parametros.append(repartidor_id)

    consulta = """
        SELECT
            e.id,
            e.pedido_id,
            p.codigo AS pedido_codigo,
            e.repartidor_id,
            r.codigo AS repartidor_codigo,
            r.nombre AS repartidor_nombre,
            e.estado AS estado_entrega,
            e.fecha_asignacion,
            e.fecha_salida,
            e.fecha_entrega,
            e.observaciones
        FROM entregas e
        JOIN pedidos p ON p.id = e.pedido_id
        JOIN repartidores r ON r.id = e.repartidor_id
    """

    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)

    consulta += " ORDER BY e.fecha_asignacion DESC, e.id DESC"

    with connect_database(db_path, read_only=True) as db:
        filas = db.execute(
            consulta,
            parametros
        ).fetchall()

        return [dict(fila) for fila in filas]


def obtener_historial_pedido(
    pedido_id,
    db_path=DEFAULT_DATABASE
):
    """Consulta el historial inmutable de estados de un pedido."""

    _validar_id(pedido_id, "pedido_id")

    with connect_database(db_path, read_only=True) as db:

        pedido = db.execute(
            "SELECT id FROM pedidos WHERE id = ?",
            (pedido_id,)
        ).fetchone()

        if pedido is None:
            raise PedidoNoEncontrado(
                "El pedido indicado no existe."
            )

        filas = db.execute(
            """
            SELECT
                id,
                pedido_id,
                estado_anterior,
                estado_nuevo,
                fecha_cambio,
                observacion
            FROM historial_estados
            WHERE pedido_id = ?
            ORDER BY fecha_cambio, id
            """,
            (pedido_id,)
        ).fetchall()

        return [dict(fila) for fila in filas]

# ============================================================
# S3-03: REGISTRO DE FECHAS E HISTORIAL DE ENTREGAS
# ============================================================

from datetime import datetime, timezone


class EntregaNoEncontrada(LookupError):
    """La entrega solicitada no existe."""


def _normalizar_fecha(fecha, campo):
    """Valida una fecha ISO 8601 y la convierte a UTC."""

    if fecha is None:
        valor = datetime.now(timezone.utc)
    else:
        if not isinstance(fecha, str):
            raise DatosEntregaInvalidos(
                f"{campo} debe ser una fecha ISO 8601."
            )

        try:
            valor = datetime.fromisoformat(
                fecha.strip().replace("Z", "+00:00")
            )
        except ValueError:
            raise DatosEntregaInvalidos(
                f"{campo} tiene un formato de fecha incorrecto."
            ) from None

        if valor.tzinfo is None:
            raise DatosEntregaInvalidos(
                f"{campo} debe incluir zona horaria."
            )

    return (
        valor.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def registrar_fecha_salida(
    entrega_id,
    fecha_salida=None,
    db_path=DEFAULT_DATABASE
):
    """Registra una única fecha de salida del repartidor."""

    _validar_id(entrega_id, "entrega_id")

    fecha = _normalizar_fecha(fecha_salida, "fecha_salida")

    with connect_database(db_path) as db:

        db.execute("BEGIN IMMEDIATE")

        entrega = db.execute(
            """
            SELECT estado, fecha_salida
            FROM entregas
            WHERE id = ?
            """,
            (entrega_id,)
        ).fetchone()

        if entrega is None:
            raise EntregaNoEncontrada(
                "La entrega indicada no existe."
            )

        if entrega["estado"] != "ASIGNADA":
            raise DatosEntregaInvalidos(
                "La salida debe registrarse antes de iniciar "
                "una transición de estado."
            )

        if entrega["fecha_salida"] is not None:
            raise DatosEntregaInvalidos(
                "La fecha de salida ya fue registrada."
            )

        db.execute(
            """
            UPDATE entregas
            SET fecha_salida = ?
            WHERE id = ?
            """,
            (fecha, entrega_id)
        )

        return _obtener_entrega_db(db, entrega_id)


def registrar_fecha_entrega(
    entrega_id,
    fecha_entrega=None,
    db_path=DEFAULT_DATABASE
):
    """Registra una única fecha de recepción del pedido."""

    _validar_id(entrega_id, "entrega_id")

    fecha = _normalizar_fecha(fecha_entrega, "fecha_entrega")

    with connect_database(db_path) as db:

        db.execute("BEGIN IMMEDIATE")

        entrega = db.execute(
            """
            SELECT estado, fecha_salida, fecha_entrega
            FROM entregas
            WHERE id = ?
            """,
            (entrega_id,)
        ).fetchone()

        if entrega is None:
            raise EntregaNoEncontrada(
                "La entrega indicada no existe."
            )

        if entrega["fecha_salida"] is None:
            raise DatosEntregaInvalidos(
                "No se puede registrar la recepción "
                "sin una fecha de salida."
            )

        if entrega["estado"] == "FALLIDA":
            raise DatosEntregaInvalidos(
                "No se puede confirmar una entrega fallida."
            )

        if entrega["fecha_entrega"] is not None:
            raise DatosEntregaInvalidos(
                "La fecha de recepción ya fue registrada."
            )

        if fecha < entrega["fecha_salida"]:
            raise DatosEntregaInvalidos(
                "La recepción no puede ser anterior a la salida."
            )

        db.execute(
            """
            UPDATE entregas
            SET fecha_entrega = ?
            WHERE id = ?
            """,
            (fecha, entrega_id)
        )

        return _obtener_entrega_db(db, entrega_id)


def obtener_historial_entrega(
    entrega_id,
    db_path=DEFAULT_DATABASE
):
    """
    Construye una línea de tiempo con las fechas de entrega
    y los cambios de estado registrados para el pedido.
    """

    _validar_id(entrega_id, "entrega_id")

    with connect_database(db_path, read_only=True) as db:

        entrega = db.execute(
            """
            SELECT
                id,
                pedido_id,
                fecha_asignacion,
                fecha_salida,
                fecha_entrega
            FROM entregas
            WHERE id = ?
            """,
            (entrega_id,)
        ).fetchone()

        if entrega is None:
            raise EntregaNoEncontrada(
                "La entrega indicada no existe."
            )

        historial = []

        historial.append({
            "fecha": entrega["fecha_asignacion"],
            "tipo": "ENTREGA_ASIGNADA",
            "estado_anterior": None,
            "estado_nuevo": "ASIGNADA",
            "observacion": "Entrega registrada."
        })

        if entrega["fecha_salida"] is not None:
            historial.append({
                "fecha": entrega["fecha_salida"],
                "tipo": "SALIDA_REPARTIDOR",
                "estado_anterior": None,
                "estado_nuevo": None,
                "observacion": "Fecha de salida registrada."
            })

        if entrega["fecha_entrega"] is not None:
            historial.append({
                "fecha": entrega["fecha_entrega"],
                "tipo": "RECEPCION_CONFIRMADA",
                "estado_anterior": None,
                "estado_nuevo": None,
                "observacion": "Fecha de recepción registrada."
            })

        cambios = db.execute(
            """
            SELECT
                fecha_cambio,
                estado_anterior,
                estado_nuevo,
                observacion
            FROM historial_estados
            WHERE pedido_id = ?
            """,
            (entrega["pedido_id"],)
        ).fetchall()

        for cambio in cambios:
            historial.append({
                "fecha": cambio["fecha_cambio"],
                "tipo": "ESTADO_PEDIDO",
                "estado_anterior": cambio["estado_anterior"],
                "estado_nuevo": cambio["estado_nuevo"],
                "observacion": cambio["observacion"]
            })

        historial.sort(key=lambda evento: evento["fecha"])

        return historial

