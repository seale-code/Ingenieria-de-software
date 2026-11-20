"""Generar el diccionario v6 desde una SQLite temporal con todas las migraciones."""
import argparse
from pathlib import Path
import tempfile

from scripts.iniciar_tienda import preparar_tienda
from src.database.database import connect_database

DESCRIPCIONES={
    'categorias':'Clasificación del catálogo.', 'productos':'Identidad y categoría del producto.',
    'sucursales':'Locales de atención y coordenadas geográficas.',
    'inventario':'Saldo físico del par producto/sucursal; disponible se calcula restando reservas activas.',
    'pedidos':'Código privado, sucursal vigente y estado operativo del pedido.',
    'detalles_pedido':'Cantidad solicitada por producto; una línea por pedido/producto.',
    'reservas_stock':'Intentos históricos de reserva. Solo una ACTIVA/CONSUMIDA por línea; LIBERADA se conserva.',
    's2_solicitudes':'Nombre de cliente, coordenadas usadas y distancia de asignación.',
    's2_capacidades':'Límite explícito de preparación por sucursal; cero deshabilita nuevas asignaciones.',
    'repartidores':'Identidad operativa y disponibilidad del repartidor; no es cuenta autenticada.',
    'entregas':'Una entrega por pedido, repartidor, estado y fechas.',
    'historial_estados':'Historial inmutable generado por cambios de estado.',
    'incidencias_pedido':'Problema, rol reportante y flujo ABIERTA → EN_REVISION → RESUELTA.',
    'catalogo_comercial':'Marca, presentación, imagen, precios en céntimos, máximo y fuente.',
    'pedidos_comerciales':'Contacto, dirección, distrito, cotización y totales confirmados; inmutable.',
    'precios_pedido':'Cantidad y precio unitario aceptados por línea; inmutable.',
    'politica_reservas':'Única configuración del plazo de futuras asignaciones (1–1440 minutos).',
    'historial_asignaciones':'Intentos inmutables de asignación, causa, origen/destino, UUID y actor.',
    'control_reservas':'Asignación vigente, límite y aceptación; control de generación para evitar acciones obsoletas.',
    'movimientos_inventario':'Apertura, entrada, ajuste o salida; saldos, variación, motivo y actor inmutables.',
}


def generar():
    lineas=['# Diccionario de datos v6','',
        'Generado con `python -m scripts.generar_diccionario` desde una base temporal migrada y el módulo de pedidos inicializado. No contiene datos de clientes ni una copia de la base operativa.','',
        '[Modelo y reglas](MODELO_DATOS.md). `NN` refleja la declaración NOT NULL de SQLite; las claves primarias tienen además su semántica propia. Los CHECK, índices parciales y triggers se consultan en las migraciones.','']
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'esquema.sqlite3';preparar_tienda(path)
        with connect_database(path,read_only=True) as db:
            tablas=[f[0] for f in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            lineas.extend([f'**{len(tablas)} tablas**, `application_id=1229867841`, `user_version=6`.',''])
            for tabla in tablas:
                lineas.extend([f'## `{tabla}`','',DESCRIPCIONES[tabla],'',
                    '| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |','|---|---|---:|---|---|'])
                for f in db.execute(f'PRAGMA table_info("{tabla}")'):
                    pred=str(f['dflt_value']).replace('|','\\|') if f['dflt_value'] is not None else '—'
                    lineas.append(f"| `{f['name']}` | {f['type']} | {f['pk']} | {'Sí' if f['notnull'] else 'No'} | {pred} |")
                fks={}
                for fk in db.execute(f'PRAGMA foreign_key_list("{tabla}")'):
                    grupo=fks.setdefault(fk['id'],dict(tabla=fk['table'],campos=[],destinos=[],borrado=fk['on_delete']))
                    grupo['campos'].append(fk['from']);grupo['destinos'].append(fk['to'])
                if fks:
                    lineas.extend(['','Claves foráneas:'])
                    for fk in fks.values():
                        lineas.append(f"- ({', '.join(fk['campos'])}) → {fk['tabla']}({', '.join(fk['destinos'])}); ON DELETE {fk['borrado']}.")
                lineas.append('')
    return '\n'.join(lineas)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida',default='docs/03-diagramas/DICCIONARIO_DATOS_V6.md')
    args=parser.parse_args();destino=Path(args.salida);destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_text(generar(),encoding='utf-8');print('Diccionario v6 generado.')


if __name__=='__main__': main()
