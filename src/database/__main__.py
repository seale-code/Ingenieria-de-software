"""Ejecutar desde la raíz del repositorio: python -m src.database --help."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .database import DEFAULT_DATABASE, get_stock, initialize_database, seed_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Base de datos del Sprint 1 de Inkafarma")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Crear o verificar el esquema sin borrar datos")
    init.add_argument("--demo", action="store_true", help="Agregar datos ficticios DEMO-*")
    seed = commands.add_parser("seed", help="Agregar datos ficticios a una base inicializada")
    stock = commands.add_parser("stock", help="Consultar stock por producto y sucursal")
    stock.add_argument("--buscar", default="", help="Parte del nombre del producto")
    stock.add_argument("--categoria", help="Código de categoría, por ejemplo DEMO-X")
    stock.add_argument("--sucursal", help="Código de sucursal, por ejemplo DEMO-NORTE")
    stock.add_argument("--solo-disponibles", action="store_true")
    for command in (init, seed, stock):
        command.add_argument("--db", type=Path, default=DEFAULT_DATABASE, help="Ruta del archivo SQLite")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            location = initialize_database(args.db, demo=args.demo)
            print(f"Base de datos lista: {location}")
        elif args.command == "seed":
            seed_demo(args.db)
            print("Datos ficticios cargados; registros existentes conservados.")
        else:
            rows = get_stock(args.db, search=args.buscar, category=args.categoria,
                             branch=args.sucursal, available_only=args.solo_disponibles)
            print(json.dumps(rows, ensure_ascii=False, indent=2))
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
