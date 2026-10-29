-- S2-04 (Anderson Delerna). Tablas aisladas del esquema S1, sin alterar user_version.
-- Contrato provisional hasta integrar las tablas definitivas de S2-03 (Josue).
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS s2_capacidades (
    sucursal_id INTEGER PRIMARY KEY REFERENCES sucursales(id) ON DELETE RESTRICT,
    capacidad_maxima INTEGER NOT NULL
        CHECK (typeof(capacidad_maxima) = 'integer' AND capacidad_maxima >= 0)
);

CREATE TABLE IF NOT EXISTS s2_pedidos (
    id INTEGER PRIMARY KEY,
    cliente TEXT NOT NULL CHECK (length(trim(cliente)) BETWEEN 1 AND 120),
    latitud REAL NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud REAL NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    sucursal_id INTEGER REFERENCES sucursales(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL CHECK (estado IN ('ASIGNADO', 'SIN_ASIGNAR',
        'EN_PREPARACION', 'EN_REPARTO', 'ENTREGADO', 'CANCELADO')),
    distancia_km REAL CHECK (distancia_km IS NULL OR distancia_km >= 0),
    motivo_sin_asignar TEXT,
    creado_en TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (
        (estado = 'SIN_ASIGNAR' AND sucursal_id IS NULL AND distancia_km IS NULL)
        OR (estado <> 'SIN_ASIGNAR' AND sucursal_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS s2_pedido_detalles (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES s2_pedidos(id) ON DELETE RESTRICT,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0),
    UNIQUE (pedido_id, producto_id)
);

-- La cantidad reservada YA se descuenta de inventario en la misma transacción;
-- esta tabla registra el movimiento, no debe descontarse una segunda vez.
CREATE TABLE IF NOT EXISTS s2_reservas (
    id INTEGER PRIMARY KEY,
    detalle_id INTEGER NOT NULL UNIQUE REFERENCES s2_pedido_detalles(id) ON DELETE RESTRICT,
    sucursal_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0),
    estado TEXT NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA','LIBERADA'))
);

CREATE INDEX IF NOT EXISTS idx_s2_pedidos_sucursal_estado
    ON s2_pedidos(sucursal_id, estado);
CREATE INDEX IF NOT EXISTS idx_s2_detalles_pedido ON s2_pedido_detalles(pedido_id);
COMMIT;
