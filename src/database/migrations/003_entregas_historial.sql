-- S3-03 / Issue #19: repartidores, entrega e historial de estados.
-- Requiere esquema v2, ejecutar con migrate_josue.py.

CREATE TABLE repartidores (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

CREATE TABLE entregas (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL UNIQUE REFERENCES pedidos(id) ON DELETE RESTRICT,
    repartidor_id INTEGER NOT NULL REFERENCES repartidores(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'ASIGNADA'
        CHECK (estado IN ('ASIGNADA','EN_CAMINO','ENTREGADA','FALLIDA')),
    fecha_asignacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    fecha_salida TEXT,
    fecha_entrega TEXT,
    observaciones TEXT,
    CHECK ((estado NOT IN ('EN_CAMINO','ENTREGADA')) OR fecha_salida IS NOT NULL),
    CHECK (estado != 'ENTREGADA' OR fecha_entrega IS NOT NULL),
    CHECK (fecha_entrega IS NULL OR (fecha_salida IS NOT NULL
                                AND fecha_entrega >= fecha_salida))
);
CREATE INDEX idx_entregas_repartidor ON entregas(repartidor_id);

CREATE TABLE historial_estados (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    estado_anterior TEXT,
    estado_nuevo TEXT NOT NULL CHECK (length(trim(estado_nuevo)) > 0),
    fecha_cambio TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    observacion TEXT
);
CREATE INDEX idx_historial_pedido_fecha ON historial_estados(pedido_id, fecha_cambio, id);

-- Registrar un punto de partida para pedidos que existían antes de Sprint 3.
INSERT INTO historial_estados (pedido_id, estado_anterior, estado_nuevo, fecha_cambio, observacion)
SELECT id, NULL, estado, fecha_creacion, 'Estado al incorporar Sprint 3'
FROM pedidos;

CREATE TRIGGER trg_pedidos_registrar_historial_inicio
AFTER INSERT ON pedidos
BEGIN
    INSERT INTO historial_estados(pedido_id, estado_anterior, estado_nuevo)
    VALUES(NEW.id, NULL, NEW.estado);
END;

CREATE TRIGGER trg_pedidos_registrar_historial_cambio
AFTER UPDATE OF estado ON pedidos
WHEN NEW.estado != OLD.estado
BEGIN
    INSERT INTO historial_estados(pedido_id, estado_anterior, estado_nuevo)
    VALUES(NEW.id, OLD.estado, NEW.estado);
END;

CREATE TRIGGER trg_historial_no_modificar
BEFORE UPDATE ON historial_estados
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados es inmutable');
END;

CREATE TRIGGER trg_historial_no_borrar
BEFORE DELETE ON historial_estados
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados no se borra');
END;
