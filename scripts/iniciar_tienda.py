"""Iniciar Inkafarma con catálogo comercial y datos persistentes.

python -m scripts.iniciar_tienda [--port 5000] [--db data/inkafarma-comercial.sqlite3]
"""
import argparse
import os
import secrets
from pathlib import Path

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor
from src.database.catalogo_comercial import cargar_catalogo
from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar


def preparar_tienda(path):
    initialize_database(path)
    migrar(path,hasta=5)
    iniciar_modulo(path)
    cargar_catalogo(path)
    with connect_database(path,read_only=True) as db:
        existen=db.execute("SELECT 1 FROM repartidores WHERE codigo='REP-01'").fetchone()
    if not existen:
        registrar_repartidor('REP-01','Equipo de reparto',path)


def main():
    parser=argparse.ArgumentParser(description='Iniciar la aplicación Inkafarma')
    parser.add_argument('--db',default='data/inkafarma-comercial.sqlite3')
    parser.add_argument('--port',type=int,default=5000)
    args=parser.parse_args()
    if not 1<=args.port<=65535:
        parser.error('El puerto debe estar entre 1 y 65535.')
    path=Path(args.db)
    preparar_tienda(path)
    key=os.environ.get('INKAFARMA_OPERATIONS_KEY') or secrets.token_urlsafe(24)
    print(f'\nTienda: http://127.0.0.1:{args.port}/\nOperaciones: http://127.0.0.1:{args.port}/operaciones\nClave de acceso al panel: {key}\n\nCtrl+C para detener el servidor. Los pedidos y el inventario se conservan.\n',flush=True)
    create_app(path,operations_key=key).run(host='127.0.0.1',port=args.port,debug=False,use_reloader=False)


if __name__=='__main__':
    main()
