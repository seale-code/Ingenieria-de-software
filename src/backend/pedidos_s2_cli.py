"""Interfaz de consola para demostrar S2-04 sin agregar dependencias web."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from src.database.database import DEFAULT_DATABASE
from src.backend.pedidos_s2 import (
    DatosInvalidos, ModuloNoInicializado, configurar_capacidad,
    iniciar_modulo, obtener_pedido, registrar_pedido,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 2 / S2-04: pedidos Inkafarma")
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE,
                        help="Base SQLite del proyecto (por defecto data/inkafarma.sqlite3)")
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser("init", help="Agregar tablas aisladas del módulo S2-04")

    capacidad = comandos.add_parser("capacidad", help="Definir capacidad máxima de una sucursal")
    capacidad.add_argument("--sucursal", required=True)
    capacidad.add_argument("--max-pedidos", type=int, required=True)

    registrar = comandos.add_parser("registrar", help="Crear y asignar un pedido")
    registrar.add_argument("--cliente", required=True)
    registrar.add_argument("--lat", type=float, required=True)
    registrar.add_argument("--lon", type=float, required=True)
    registrar.add_argument("--item", action="append", required=True,
                           help="Código:cantidad; repetir para varios productos")

    consultar = comandos.add_parser("consultar", help="Consultar un pedido persistido")
    consultar.add_argument("--pedido", type=int, required=True)

    args = parser.parse_args(argv)
    try:
        if args.comando == "init":
            iniciar_modulo(args.db)
            salida = {"resultado": "Módulo S2-04 inicializado", "base": str(args.db)}
        elif args.comando == "capacidad":
            salida = configurar_capacidad(args.sucursal, args.max_pedidos, args.db)
        elif args.comando == "registrar":
            items = []
            for texto in args.item:
                codigo, sep, cantidad = texto.rpartition(":")
                if not sep or not codigo or not cantidad.isdecimal():
                    raise DatosInvalidos("Cada --item debe tener el formato CODIGO:CANTIDAD.")
                items.append({"producto_codigo": codigo, "cantidad": int(cantidad)})
            salida = registrar_pedido({"cliente": args.cliente, "latitud": args.lat,
                                       "longitud": args.lon, "items": items}, args.db)
        else:
            salida = obtener_pedido(args.pedido, args.db)
            if salida is None:
                raise DatosInvalidos("Pedido no encontrado.")
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return 0
    except (DatosInvalidos, ModuloNoInicializado, ValueError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
