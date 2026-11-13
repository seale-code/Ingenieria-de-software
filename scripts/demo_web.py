"""Demostración aislada: python -m scripts.demo_web [--port 5000].

Solo escucha en 127.0.0.1. La base temporal y la clave nueva duran hasta Ctrl+C.
No acepta una ruta a bases del usuario ni modifica data/inkafarma.sqlite3.
"""
import argparse
import secrets
import tempfile
from pathlib import Path

from src.backend.app import create_app
from src.backend.entregas_s3 import registrar_entrega
from src.backend.pedidos_s2 import iniciar_modulo, registrar_pedido
from src.backend.preparacion_pedidos import iniciar_preparacion_pedido, completar_preparacion_pedido
from src.backend.repartidores_s3 import registrar_repartidor
from src.backend.reparto_integrado import avanzar_reparto
from src.backend.soporte_pedidos_s3 import registrar_incidencia
from src.database.database import initialize_database, connect_database
from src.database.migrate_josue import migrar


def preparar_demo(path):
    """Solo se llama sobre el archivo recién creado del directorio temporal."""
    initialize_database(path, demo=True)
    migrar(path, hasta=4)
    iniciar_modulo(path)
    with connect_database(path) as db:
        db.execute("UPDATE inventario SET cantidad=20 WHERE producto_id=(SELECT id FROM productos WHERE codigo='DEMO-A') AND sucursal_id=(SELECT id FROM sucursales WHERE codigo='DEMO-NORTE')")
        db.execute("INSERT INTO categorias(codigo,nombre) VALUES('DEMO-CUIDADO','Cuidado personal demo')")
        for code, name, stock in [('DEMO-D','Gel de higiene demo',18),('DEMO-E','Jabón de cuidado demo',12),('DEMO-F','Kit de higiene demo',8)]:
            product = db.execute("INSERT INTO productos(codigo,nombre,categoria_id) SELECT ?,?,id FROM categorias WHERE codigo='DEMO-CUIDADO'", (code,name)).lastrowid
            db.execute('INSERT INTO inventario(producto_id,sucursal_id,cantidad) SELECT ?,id,? FROM sucursales', (product,stock))
    driver = registrar_repartidor('DEMO-REP-01','Alex · Repartidor demo',path)
    registrar_repartidor('DEMO-REP-02','Sam · Repartidor demo',path)
    for name, stage in [('Cliente demo · Entrega','EN_CAMINO'),('Cliente demo · Preparado','PREPARADO'),('Cliente demo · Nuevo','ASIGNADO')]:
        pedido = registrar_pedido(dict(cliente=name,latitud=-12.0,longitud=-77.05,
            items=[dict(producto_codigo='DEMO-A',cantidad=1)]),path)
        if stage != 'ASIGNADO':
            iniciar_preparacion_pedido(pedido['pedido_id'],path)
            completar_preparacion_pedido(pedido['pedido_id'],path)
        if stage == 'EN_CAMINO':
            registrar_entrega(pedido['pedido_id'],driver['id'],db_path=path)
            avanzar_reparto(pedido['pedido_id'],'EN_CAMINO','REPARTIDOR',driver['id'],path)
            registrar_incidencia(pedido['pedido_id'],'RETRASO','Retraso ficticio para demostrar el módulo de soporte.',
                                'REPARTIDOR',driver['id'],path)


def main():
    parser = argparse.ArgumentParser(description='Abrir la demo web local del Sprint 3')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('El puerto debe estar entre 1 y 65535.')
    with tempfile.TemporaryDirectory(prefix='inkafarma-demo-web-') as directory:
        path = Path(directory) / 'demo.sqlite3'
        preparar_demo(path)
        key = secrets.token_urlsafe(24)
        print(f'\nCatálogo: http://127.0.0.1:{args.port}/\nPanel: http://127.0.0.1:{args.port}/operaciones\nClave de esta demostración: {key}\n\nDatos ficticios y temporales. Ctrl+C para terminar.\n', flush=True)
        create_app(path,demo_key=key).run(host='127.0.0.1',port=args.port,debug=False,use_reloader=False)


if __name__ == '__main__':
    main()
