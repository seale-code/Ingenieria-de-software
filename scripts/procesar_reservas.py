"""Punto de entrada para cron/WSGI: python -m scripts.procesar_reservas --db ..."""
import argparse
import json

from src.backend.logistica import procesar_vencimientos


def main():
    parser = argparse.ArgumentParser(description='Procesar un lote de reservas pendientes vencidas')
    parser.add_argument('--db', default='data/inkafarma-comercial.sqlite3')
    args = parser.parse_args()
    resultados = procesar_vencimientos(args.db)
    print(json.dumps(dict(procesados=len(resultados), resultados=resultados), ensure_ascii=False))


if __name__ == '__main__':
    main()
