"""Iniciar Inkafarma con catálogo comercial y datos persistentes.

python -m scripts.iniciar_tienda [--port 5000] [--db data/inkafarma-comercial.sqlite3]
"""
import argparse
import os
from pathlib import Path

from src.backend.app import create_app
from src.backend.pedidos_s2 import iniciar_modulo
from src.backend.repartidores_s3 import registrar_repartidor
from src.backend.logistica import configurar_plazo
from src.backend.vencimientos import vigilar_reservas
from src.database.catalogo_comercial import cargar_catalogo
from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar


def preparar_tienda(path):
    initialize_database(path)
    migrar(path,hasta=6)
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
    parser.add_argument('--reserva-minutos',type=int,help='Plazo para nuevas asignaciones (1–1440; inicial: 15)')
    args=parser.parse_args()
    if not 1<=args.port<=65535:
        parser.error('El puerto debe estar entre 1 y 65535.')
    if args.reserva_minutos is not None and not 1<=args.reserva_minutos<=1440:
        parser.error('El plazo de reserva debe estar entre 1 y 1440 minutos.')
    path=Path(args.db)
    preparar_tienda(path)
    if args.reserva_minutos is not None:
        configurar_plazo(args.reserva_minutos,path)
    if os.environ.get('INKAFARMA_PERFIL') == 'produccion':
        parser.error('Utiliza el servidor WSGI con TLS para producción.')
    print(f'Tienda: http://127.0.0.1:{args.port}/ · Panel: /operaciones',flush=True)
    print(f'Cuenta personal: python -m scripts.operadores --db "{path}" guardar USUARIO --central')
    with vigilar_reservas(path):
        create_app(path).run(host='127.0.0.1',port=args.port,debug=False,use_reloader=False)


if __name__=='__main__':
    main()
