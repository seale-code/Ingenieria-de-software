"""Creación y consulta de la base del Sprint 1, sin dependencias externas."""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

SQL_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_DATABASE = SQL_DIRECTORY.parents[1] / "data" / "inkafarma.sqlite3"
APPLICATION_ID = 1229867841
SCHEMA_VERSION = 1


def _validate_database(db: sqlite3.Connection) -> None:
    if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
        raise ValueError("La base no pertenece a este esquema. Usa init sobre una ruta nueva.")
    if db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
        raise ValueError("Versión de base de datos no soportada; no se modificaron los datos.")


@contextmanager
def connect_database(path: str | Path, *, read_only: bool = False):
    """Abre una base existente, valida su versión, confirma/rollback y cierra."""
    location = Path(path).expanduser().resolve()
    if not location.is_file():
        raise ValueError(f"No existe la base {location}. Créala primero con init.")
    mode = "ro" if read_only else "rw"
    db = sqlite3.connect(location.as_uri() + f"?mode={mode}", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        _validate_database(db)
        with db:
            yield db
    finally:
        db.close()


def initialize_database(path: str | Path = DEFAULT_DATABASE, *, demo: bool = False) -> Path:
    """Crea un esquema nuevo o conserva uno compatible, sin borrar información."""
    location = Path(path).expanduser().resolve()
    location.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(location)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        app_id = db.execute("PRAGMA application_id").fetchone()[0]
        version = db.execute("PRAGMA user_version").fetchone()[0]
        objects = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchone()[0]
        if app_id == 0 and version == 0 and objects == 0:
            with db:
                db.executescript((SQL_DIRECTORY / "schema.sql").read_text(encoding="utf-8"))
        else:
            _validate_database(db)
    if demo:
        seed_demo(location)
    return location


def seed_demo(path: str | Path = DEFAULT_DATABASE) -> None:
    """Carga los códigos ficticios DEMO-* sin sobrescribir registros existentes."""
    with connect_database(path) as db:
        db.executescript((SQL_DIRECTORY / "seed.sql").read_text(encoding="utf-8"))


def get_stock(
    path: str | Path = DEFAULT_DATABASE,
    *,
    search: str = "",
    category: str | None = None,
    branch: str | None = None,
    available_only: bool = False,
) -> list[dict]:
    """Consulta filas producto/sucursal; una búsqueda vacía incluye todas.

    Categoría y sucursal se filtran por código exacto. La búsqueda parcial
    distingue acentos, pero no mayúsculas; %, _ y apóstrofos son literales.
    Las sucursales sin un registro de inventario no aparecen en esta vista.
    """
    conditions = ["instr(casefold(producto), casefold(?)) > 0"]
    parameters: list = [search.strip()]
    if category is not None:
        conditions.append("categoria_codigo = ?")
        parameters.append(category)
    if branch is not None:
        conditions.append("sucursal_codigo = ?")
        parameters.append(branch)
    if available_only:
        conditions.append("cantidad > 0")
    query = (
        "SELECT * FROM v_disponibilidad WHERE "
        + " AND ".join(conditions)
        + " ORDER BY producto_codigo, sucursal_codigo"
    )
    with connect_database(path, read_only=True) as db:
        db.create_function("casefold", 1, str.casefold, deterministic=True)
        return [dict(row) for row in db.execute(query, parameters).fetchall()]
