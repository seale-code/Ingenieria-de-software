"""Migraciones incrementales de las tareas de Josue, sin destruir la BD v1.

Uso (desde la raíz del proyecto):
    python -m src.database.migrate_josue --db data/inkafarma.sqlite3

Para el usuario con código del Sprint 1, aplicar primero
`compatibilidad_versiones.patch` a src/database/database.py.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

APPLICATION_ID = 1229867841
DIRECTORY = Path(__file__).resolve().parent / 'migrations'
DEFAULT_DB = Path('data/inkafarma.sqlite3')
MIGRATIONS = (
    (2, '002_pedidos_reservas.sql'),
    (3, '003_entregas_historial.sql'),
)

def migrar(ruta: str | Path, hasta: int = 3) -> list[int]:
    """Migra una BD existente, preserva datos, y detiene errores sin recrearla."""
    archivo = Path(ruta).expanduser().resolve()
    if not archivo.is_file():
        raise ValueError(f'No existe la base {archivo}; inicialícela antes con --demo.')
    if hasta not in (2, 3):
        raise ValueError('La versión destino debe ser 2 o 3.')
    avanzadas: list[int] = []
    # El contexto de sqlite3 confirma/revierte transacciones, pero NO cierra
    # automáticamente la conexión. closing() la libera también si hay error.
    with closing(sqlite3.connect(archivo.as_uri() + '?mode=rw', uri=True, timeout=15)) as db, db:
        db.execute('PRAGMA foreign_keys = ON')
        id_actual = db.execute('PRAGMA application_id').fetchone()[0]
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if id_actual != APPLICATION_ID or version not in (1, 2, 3):
            raise ValueError('BD ajena o versión no admitida: operación cancelada.')
        if version > hasta:
            raise ValueError('La base ya tiene una versión mayor. No se realizan retrocesos.')
        for numero, archivo_sql in MIGRATIONS:
            if numero <= version or numero > hasta:
                continue
            texto = (DIRECTORY / archivo_sql).read_text(encoding='utf-8')
            try:
                db.executescript(
                    'BEGIN IMMEDIATE;\n' + texto +
                    f'\nPRAGMA user_version = {numero};\nCOMMIT;\n'
                )
            except Exception:
                if db.in_transaction:
                    db.rollback()
                raise
            version = numero
            avanzadas.append(numero)
    return avanzadas

def main() -> int:
    parser = argparse.ArgumentParser(description='Migrar esquema Inkafarma v1 a v2/v3')
    parser.add_argument('--db', default=str(DEFAULT_DB))
    parser.add_argument('--hasta', type=int, choices=[2, 3], default=3)
    opciones = parser.parse_args()
    try:
        avanzadas = migrar(opciones.db, opciones.hasta)
        if avanzadas:
            print('Migraciones aplicadas:', ', '.join(map(str, avanzadas)))
        else:
            print('Base ya actualizada; no hay cambios.')
        return 0
    except (ValueError, sqlite3.Error, OSError) as error:
        print('Error:', error, file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
