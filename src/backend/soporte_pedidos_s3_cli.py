"""CLI sencilla para demostrar el soporte y los estados del S3-04."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from src.database.database import DEFAULT_DATABASE
from src.database.migrate_josue import migrar
from src.backend.entregas_s3 import registrar_fecha_salida, registrar_fecha_entrega
from src.backend.soporte_pedidos_s3 import (
    actualizar_estado_incidencia,
    cancelar_pedido,
    cambiar_estado_pedido,
    listar_incidencias,
    registrar_incidencia,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Demostración del soporte y seguimiento de pedidos S3-04."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    commands = parser.add_subparsers(dest="comando", required=True)

    commands.add_parser("migrar", help="Aplicar la migración de soporte hasta v4")

    salida = commands.add_parser("salida", help="Registrar la salida del repartidor")
    salida.add_argument("--entrega", type=int, required=True)
    salida.add_argument("--fecha")

    cambio = commands.add_parser("cambiar-estado", help="Cambiar estado de reparto")
    cambio.add_argument("--pedido", type=int, required=True)
    cambio.add_argument("--estado", choices=["EN_CAMINO", "ENTREGADO"], required=True)
    cambio.add_argument("--rol", default="REPARTIDOR")
    cambio.add_argument("--actor-id", type=int, required=True)

    recepcion = commands.add_parser("recepcion", help="Registrar la recepción del pedido")
    recepcion.add_argument("--entrega", type=int, required=True)
    recepcion.add_argument("--fecha")

    cancelar = commands.add_parser("cancelar", help="Cancelar un pedido antes de su salida")
    cancelar.add_argument("--pedido", type=int, required=True)
    cancelar.add_argument("--rol", default="ADMINISTRADOR")
    cancelar.add_argument("--actor-id", type=int)

    incidencia = commands.add_parser("incidencia", help="Registrar una incidencia")
    incidencia.add_argument("--pedido", type=int, required=True)
    incidencia.add_argument("--categoria", required=True)
    incidencia.add_argument("--descripcion", required=True)
    incidencia.add_argument("--rol", required=True)
    incidencia.add_argument("--actor-id", type=int)

    listar = commands.add_parser("listar-incidencias", help="Consultar incidencias permitidas por rol")
    listar.add_argument("--rol", required=True)
    listar.add_argument("--actor-id", type=int)
    listar.add_argument("--estado", choices=["ABIERTA", "EN_REVISION", "RESUELTA"])

    atender = commands.add_parser("atender-incidencia", help="Avanzar una incidencia")
    atender.add_argument("--incidencia", type=int, required=True)
    atender.add_argument("--estado", choices=["EN_REVISION", "RESUELTA"], required=True)
    atender.add_argument("--rol", required=True)
    atender.add_argument("--actor-id", type=int)
    atender.add_argument("--resolucion")

    args = parser.parse_args(argv)

    try:
        if args.comando == "migrar":
            resultado = migrar(args.db, hasta=4)
            salida_json = {"migraciones_aplicadas": resultado, "version_destino": 4}
        elif args.comando == "salida":
            salida_json = registrar_fecha_salida(args.entrega, args.fecha, args.db)
        elif args.comando == "cambiar-estado":
            salida_json = cambiar_estado_pedido(
                args.pedido, args.estado, args.rol, args.actor_id, args.db
            )
        elif args.comando == "recepcion":
            salida_json = registrar_fecha_entrega(args.entrega, args.fecha, args.db)
        elif args.comando == "cancelar":
            salida_json = cancelar_pedido(
                args.pedido, args.rol, args.actor_id, args.db
            )
        elif args.comando == "incidencia":
            salida_json = registrar_incidencia(
                args.pedido, args.categoria, args.descripcion,
                args.rol, args.actor_id, args.db
            )
        elif args.comando == "listar-incidencias":
            salida_json = listar_incidencias(
                args.rol, args.actor_id, args.estado, db_path=args.db
            )
        else:
            salida_json = actualizar_estado_incidencia(
                args.incidencia, args.estado, args.rol, args.actor_id,
                args.resolucion, args.db
            )
        print(json.dumps(salida_json, ensure_ascii=False, indent=2))
        return 0
    except (OSError, sqlite3.Error, ValueError, LookupError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
