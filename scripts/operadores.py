"""Administrar cuentas y atender verificaciones telefónicas desde un equipo autorizado."""
import argparse
from getpass import getpass
import time

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.seguridad import emitir_codigo, guardar_usuario
from src.database.database import connect_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='data/inkafarma-comercial.sqlite3')
    comandos=parser.add_subparsers(dest='accion',required=True)
    alta=comandos.add_parser('guardar')
    alta.add_argument('usuario')
    grupo=alta.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--central',action='store_true')
    grupo.add_argument('--sucursal')
    comandos.add_parser('revocar').add_argument('usuario')
    comandos.add_parser('llamadas')
    comandos.add_parser('llamar').add_argument('solicitud')
    args=parser.parse_args()
    preparar_tienda(args.db)
    app=create_app(args.db)
    with app.app_context():
        if args.accion=='guardar':
            guardar_usuario(args.db,args.usuario,getpass('Contraseña personal: '),args.sucursal)
        elif args.accion=='revocar':
            with connect_database(args.db) as db:
                db.execute('DELETE FROM operadores WHERE usuario=?',(args.usuario,))
        elif args.accion=='llamadas':
            with connect_database(args.db) as db:
                db.execute('DELETE FROM verificaciones WHERE hasta<=?',(int(time.time()),))
                for fila in db.execute('SELECT solicitud FROM verificaciones WHERE digest IS NULL ORDER BY hasta'):
                    print(fila['solicitud'])
        else:
            telefono,codigo=emitir_codigo(args.solicitud)
            print(f'Llama al {telefono}. Comunica el código {codigo} solo a quien atienda ese número.')


if __name__=='__main__':
    main()
