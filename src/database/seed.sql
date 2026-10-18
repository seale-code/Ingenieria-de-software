-- Datos exclusivamente ficticios; los códigos DEMO-* se reservan para esta carga.
-- Los conflictos por código/par se conservan: no se sobrescribe un stock editado.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT INTO categorias (codigo, nombre) VALUES
    ('DEMO-X', 'Categoría demo X'), ('DEMO-Y', 'Categoría demo Y')
ON CONFLICT(codigo) DO NOTHING;

INSERT INTO productos (codigo, nombre, categoria_id) VALUES
    ('DEMO-A', 'Producto demo A', (SELECT id FROM categorias WHERE codigo = 'DEMO-X')),
    ('DEMO-B', 'Producto demo B', (SELECT id FROM categorias WHERE codigo = 'DEMO-Y')),
    ('DEMO-C', 'Producto demo C', (SELECT id FROM categorias WHERE codigo = 'DEMO-X'))
ON CONFLICT(codigo) DO NOTHING;

INSERT INTO sucursales (codigo, nombre, latitud, longitud) VALUES
    ('DEMO-NORTE', 'Sucursal demo Norte', -12.000, -77.050),
    ('DEMO-SUR', 'Sucursal demo Sur', -12.100, -77.030)
ON CONFLICT(codigo) DO NOTHING;

INSERT INTO inventario (producto_id, sucursal_id, cantidad) VALUES
    ((SELECT id FROM productos WHERE codigo = 'DEMO-A'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-NORTE'), 5),
    ((SELECT id FROM productos WHERE codigo = 'DEMO-A'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-SUR'), 0),
    ((SELECT id FROM productos WHERE codigo = 'DEMO-B'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-NORTE'), 0),
    ((SELECT id FROM productos WHERE codigo = 'DEMO-B'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-SUR'), 3),
    ((SELECT id FROM productos WHERE codigo = 'DEMO-C'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-NORTE'), 0),
    ((SELECT id FROM productos WHERE codigo = 'DEMO-C'), (SELECT id FROM sucursales WHERE codigo = 'DEMO-SUR'), 0)
ON CONFLICT(producto_id, sucursal_id) DO NOTHING;

COMMIT;
