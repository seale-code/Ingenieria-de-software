"""S3-03: gestión de repartidores de Inkafarma."""

import sqlite3

from src.database.database import DEFAULT_DATABASE, connect_database


class DatosInvalidos(ValueError):
    """Datos incorrectos para registrar un repartidor."""


class RepartidorNoEncontrado(LookupError):
    """El repartidor solicitado no existe."""


def _validar_texto(valor, campo, maximo):
    if not isinstance(valor, str):
        raise DatosInvalidos(f"{campo} debe ser texto.")

    valor = valor.strip()

    if not valor:
        raise DatosInvalidos(f"{campo} es obligatorio.")

    if len(valor) > maximo:
        raise DatosInvalidos(
            f"{campo} no puede superar {maximo} caracteres."
        )

    return valor


def _validar_id(repartidor_id):
    if (
        isinstance(repartidor_id, bool)
        or not isinstance(repartidor_id, int)
        or repartidor_id <= 0
    ):
        raise DatosInvalidos("El ID debe ser un entero positivo.")


def registrar_repartidor(
    codigo,
    nombre,
    db_path=DEFAULT_DATABASE
):
    """Registra un nuevo repartidor."""

    codigo = _validar_texto(codigo, "codigo", 80)
    nombre = _validar_texto(nombre, "nombre", 120)

    try:
        with connect_database(db_path) as db:
            db.execute("BEGIN IMMEDIATE")

            cursor = db.execute(
                """
                INSERT INTO repartidores (codigo, nombre)
                VALUES (?, ?)
                """,
                (codigo, nombre)
            )

            repartidor_id = cursor.lastrowid

            fila = db.execute(
                """
                SELECT id, codigo, nombre, activo
                FROM repartidores
                WHERE id = ?
                """,
                (repartidor_id,)
            ).fetchone()

            return dict(fila)

    except sqlite3.IntegrityError as error:
        if "UNIQUE" in str(error).upper():
            raise DatosInvalidos(
                "Ya existe un repartidor con ese código."
            ) from None
        raise


def listar_repartidores(
    activo=None,
    db_path=DEFAULT_DATABASE
):
    """Lista todos los repartidores o filtra por estado."""

    if activo is not None and not isinstance(activo, bool):
        raise DatosInvalidos("activo debe ser verdadero o falso.")

    with connect_database(db_path, read_only=True) as db:

        if activo is None:
            filas = db.execute(
                """
                SELECT id, codigo, nombre, activo
                FROM repartidores
                ORDER BY nombre, id
                """
            ).fetchall()

        else:
            filas = db.execute(
                """
                SELECT id, codigo, nombre, activo
                FROM repartidores
                WHERE activo = ?
                ORDER BY nombre, id
                """,
                (int(activo),)
            ).fetchall()

        return [dict(fila) for fila in filas]


def obtener_repartidor(
    repartidor_id,
    db_path=DEFAULT_DATABASE
):
    """Consulta un repartidor por su ID."""

    _validar_id(repartidor_id)

    with connect_database(db_path, read_only=True) as db:

        fila = db.execute(
            """
            SELECT id, codigo, nombre, activo
            FROM repartidores
            WHERE id = ?
            """,
            (repartidor_id,)
        ).fetchone()

        return dict(fila) if fila else None


def actualizar_repartidor(
    repartidor_id,
    nombre=None,
    activo=None,
    db_path=DEFAULT_DATABASE
):
    """Actualiza nombre o disponibilidad del repartidor."""

    _validar_id(repartidor_id)

    cambios = []
    parametros = []

    if nombre is not None:
        nombre = _validar_texto(nombre, "nombre", 120)
        cambios.append("nombre = ?")
        parametros.append(nombre)

    if activo is not None:

        if not isinstance(activo, bool):
            raise DatosInvalidos("activo debe ser verdadero o falso.")

        cambios.append("activo = ?")
        parametros.append(int(activo))

    if not cambios:
        raise DatosInvalidos(
            "Debes indicar el nombre o el estado que deseas modificar."
        )

    parametros.append(repartidor_id)

    with connect_database(db_path) as db:

        cursor = db.execute(
            f"""
            UPDATE repartidores
            SET {", ".join(cambios)}
            WHERE id = ?
            """,
            parametros
        )

        if cursor.rowcount == 0:
            raise RepartidorNoEncontrado(
                "No existe el repartidor indicado."
            )

        fila = db.execute(
            """
            SELECT id, codigo, nombre, activo
            FROM repartidores
            WHERE id = ?
            """,
            (repartidor_id,)
        ).fetchone()

        return dict(fila)
