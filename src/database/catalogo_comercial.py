"""Carga inicial idempotente del catálogo; conserva precios y stock operados."""
import json
from pathlib import Path

from src.database.database import connect_database

PRODUCTOS = Path(__file__).with_name('catalogo') / 'productos.json'
CATEGORIAS = {
    'DERMO':'Dermocosmética', 'SOLAR':'Protección solar', 'SALUD':'Medicamentos',
    'PERSONAL':'Cuidado personal', 'BEBE':'Bebés y maternidad',
}
CENTROS = (
    ('MIRAFLORES','Miraflores',-12.1211,-77.0294),
    ('SAN-ISIDRO','San Isidro',-12.0972,-77.0363),
    ('SURCO','Santiago de Surco',-12.1343,-76.9868),
)


def cargar_catalogo(path):
    productos=json.loads(PRODUCTOS.read_text(encoding='utf-8'))
    with connect_database(path) as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('PRAGMA user_version').fetchone()[0] != 5:
            raise ValueError('Aplica las migraciones hasta la versión 5 antes de cargar el catálogo.')
        for codigo,nombre in CATEGORIAS.items():
            db.execute('INSERT INTO categorias(codigo,nombre) VALUES(?,?) ON CONFLICT(codigo) DO NOTHING',(codigo,nombre))
        for centro in CENTROS:
            db.execute('INSERT INTO sucursales(codigo,nombre,latitud,longitud) VALUES(?,?,?,?) ON CONFLICT(codigo) DO NOTHING',centro)
        for indice,p in enumerate(productos):
            db.execute('''INSERT INTO productos(codigo,nombre,categoria_id)
                SELECT ?,?,id FROM categorias WHERE codigo=? ON CONFLICT(codigo) DO NOTHING''',
                (p['codigo'],p['nombre'],p['categoria']))
            producto_id=db.execute('SELECT id FROM productos WHERE codigo=?',(p['codigo'],)).fetchone()[0]
            db.execute('''INSERT INTO catalogo_comercial(producto_id,marca,presentacion,descripcion,imagen,orden,
                precio_centimos,precio_lista_centimos,maximo,fuente,fecha_fuente)
                VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(producto_id) DO NOTHING''',
                (producto_id,p['marca'],p['presentacion'],p['descripcion'],p['imagen'],indice,p['precio_centimos'],
                 p['precio_lista_centimos'],p['maximo'],p['fuente'],p['consultado']))
            for codigo,_,_,_ in CENTROS:
                db.execute('''INSERT INTO inventario(producto_id,sucursal_id,cantidad)
                    SELECT ?,id,? FROM sucursales WHERE codigo=?
                    ON CONFLICT(producto_id,sucursal_id) DO NOTHING''',(producto_id,18+(indice%5)*4,codigo))
