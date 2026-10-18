-- Sprint 1. Ejecutar solamente sobre una base nueva mediante el módulo Python.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE categorias (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0)
);

CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT
);

CREATE TABLE sucursales (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    latitud REAL NOT NULL CHECK (typeof(latitud) IN ('real', 'integer') AND latitud BETWEEN -90 AND 90),
    longitud REAL NOT NULL CHECK (typeof(longitud) IN ('real', 'integer') AND longitud BETWEEN -180 AND 180)
);

CREATE TABLE inventario (
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    sucursal_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad >= 0),
    PRIMARY KEY (producto_id, sucursal_id)
);

CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_inventario_sucursal ON inventario(sucursal_id);

CREATE VIEW v_disponibilidad AS
SELECT p.codigo AS producto_codigo, p.nombre AS producto,
       c.codigo AS categoria_codigo, c.nombre AS categoria,
       s.codigo AS sucursal_codigo, s.nombre AS sucursal,
       s.latitud, s.longitud, i.cantidad
FROM inventario AS i
JOIN productos AS p ON p.id = i.producto_id
JOIN categorias AS c ON c.id = p.categoria_id
JOIN sucursales AS s ON s.id = i.sucursal_id;

-- Identifica el esquema de este proyecto; no es una credencial.
PRAGMA application_id = 1229867841;
PRAGMA user_version = 1;
COMMIT;
