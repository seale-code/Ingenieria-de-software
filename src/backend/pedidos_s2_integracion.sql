-- Complemento del esquema v2/v3: configuración y datos de la solicitud.
-- Los pedidos, detalles y reservas se guardan en las tablas de Josué.
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS s2_capacidades (
    sucursal_id INTEGER PRIMARY KEY REFERENCES sucursales(id) ON DELETE RESTRICT,
    capacidad_maxima INTEGER NOT NULL
        CHECK (typeof(capacidad_maxima) = 'integer' AND capacidad_maxima >= 0)
);
CREATE TABLE IF NOT EXISTS s2_solicitudes (
    pedido_id INTEGER PRIMARY KEY REFERENCES pedidos(id) ON DELETE RESTRICT,
    cliente TEXT NOT NULL CHECK (length(trim(cliente)) BETWEEN 1 AND 120),
    latitud REAL NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud REAL NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    distancia_km REAL NOT NULL CHECK (distancia_km >= 0)
);
COMMIT;
