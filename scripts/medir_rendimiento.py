"""Medición acotada de Flask/SQLite en proceso local y base temporal."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import platform
import statistics
import tempfile
from time import perf_counter

from scripts.iniciar_tienda import preparar_tienda
from src.backend.app import create_app
from src.backend.pedidos_s2 import registrar_pedido
from scripts.respaldo_base import copiar


def medir(muestras=30):
    if not 10<=muestras<=500: raise ValueError('Las muestras deben estar entre 10 y 500.')
    with tempfile.TemporaryDirectory() as carpeta:
        path=Path(carpeta)/'medicion.sqlite3';preparar_tienda(path)
        cliente=create_app(path).test_client()
        def catalogo():
            respuesta=cliente.get('/api/catalogo')
            if respuesta.status_code!=200: raise RuntimeError('Falló el catálogo durante la medición.')
            respuesta.close()
        for _ in range(5): catalogo()
        tiempos=[]
        for _ in range(muestras):
            inicio=perf_counter();catalogo();tiempos.append((perf_counter()-inicio)*1000)
        def pedido(_):
            return registrar_pedido(dict(cliente='Carga local',latitud=-12.1211,longitud=-77.0294,
                items=[dict(producto_codigo='023735',cantidad=1)]),path)
        inicio=perf_counter()
        with ThreadPoolExecutor(max_workers=4) as pool: pedidos=list(pool.map(pedido,range(12)))
        concurrencia_ms=(perf_counter()-inicio)*1000
        if any(p['pedido_id'] is None for p in pedidos): raise RuntimeError('El escenario esperaba 12 pedidos asignados.')
        inicio=perf_counter();recuperacion=copiar(path,Path(carpeta)/'respaldo.sqlite3');copia_ms=(perf_counter()-inicio)*1000
        return dict(fecha_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
            sistema=platform.system(),arquitectura=platform.machine(),esquema=6,
            alcance='Flask test_client en proceso local; no mide red, WSGI de producción ni operación real de Inkafarma',
            catalogo=dict(productos=16,sucursales=3,calentamiento=5,muestras=muestras,
                p50_ms=round(statistics.median(tiempos),3),p95_ms=round(sorted(tiempos)[math.ceil(.95*muestras)-1],3),
                max_ms=round(max(tiempos),3)),
            pedidos_servicio=dict(hilos=4,solicitudes=12,asignados=len(pedidos),duracion_total_ms=round(concurrencia_ms,3)),
            respaldo=dict(duracion_ms=round(copia_ms,3),**recuperacion))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--muestras',type=int,default=30)
    args=parser.parse_args();print(json.dumps(medir(args.muestras),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
