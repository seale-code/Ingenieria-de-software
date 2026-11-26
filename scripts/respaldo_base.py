"""Copiar/restaurar SQLite a una ruta nueva, con validación y sin sobrescritura."""
import argparse
import json
import os
from pathlib import Path
import sqlite3

from src.database.database import connect_database


def verificar(ruta):
    with connect_database(ruta, read_only=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('La base no supera la verificación de integridad.')
        return dict(esquema=db.execute('PRAGMA user_version').fetchone()[0], integridad='ok', claves_foraneas='ok')


def copiar(origen, destino):
    origen=Path(origen).expanduser().resolve(); destino=Path(destino).expanduser().resolve()
    if origen == destino:
        raise ValueError('El destino debe ser una ruta nueva distinta del origen.')
    verificar(origen)
    destino.parent.mkdir(parents=True,exist_ok=True)
    # O_EXCL evita que una carrera sobrescriba un archivo creado por otro proceso.
    descriptor=os.open(destino,os.O_CREAT | os.O_EXCL | os.O_WRONLY,0o600)
    os.close(descriptor)
    try:
        with connect_database(origen,read_only=True) as fuente:
            copia=sqlite3.connect(destino)
            try:
                fuente.backup(copia)
            finally:
                copia.close()
        return verificar(destino)
    except Exception:
        destino.unlink(missing_ok=True)
        raise


def main():
    parser=argparse.ArgumentParser(description='Respaldo/restauración a archivo nuevo; no sobrescribe datos')
    parser.add_argument('operacion',choices=['crear','restaurar','verificar'])
    parser.add_argument('--origen',required=True)
    parser.add_argument('--destino')
    args=parser.parse_args()
    if args.operacion != 'verificar' and not args.destino:
        parser.error('crear/restaurar requieren --destino con una ruta nueva.')
    try:
        resultado=verificar(args.origen) if args.operacion=='verificar' else copiar(args.origen,args.destino)
        print(json.dumps(dict(operacion=args.operacion,**resultado),ensure_ascii=False))
    except (ValueError,OSError,sqlite3.Error) as error:
        parser.exit(1,f'No se completó la operación: {error}\n')


if __name__=='__main__': main()
