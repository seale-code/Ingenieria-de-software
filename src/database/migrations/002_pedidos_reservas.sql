-- S2-03 / Issue #21: tablas de pedidos, detalles y reservas.
-- Ejecutar exclusivamente con migrate_josue.py sobre el esquema v1.

CREATE TABLE pedidos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (length(trim(codigo)) > 0),
    sucursal_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'REGISTRADO'
        CHECK (estado IN ('REGISTRADO','ASIGNADO','EN_PREPARACION','PREPARADO',
                         'EN_CAMINO','ENTREGADO','CANCELADO')),
    fecha_creacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE (id, sucursal_id)
);
CREATE INDEX idx_pedidos_sucursal_estado ON pedidos(sucursal_id, estado);

CREATE TABLE detalles_pedido (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0),
    UNIQUE (pedido_id, producto_id),
    UNIQUE (id, pedido_id, producto_id)
);
CREATE INDEX idx_detalles_producto ON detalles_pedido(producto_id);

CREATE TABLE reservas_stock (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    sucursal_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0),
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA','CONSUMIDA','LIBERADA')),
    fecha_creacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    fecha_cierre TEXT,
    fecha_vencimiento TEXT,
    UNIQUE(pedido_id, producto_id),
    FOREIGN KEY(pedido_id, producto_id) REFERENCES detalles_pedido(pedido_id, producto_id)
        ON DELETE RESTRICT,
    FOREIGN KEY(pedido_id, sucursal_id) REFERENCES pedidos(id, sucursal_id)
        ON DELETE RESTRICT,
    FOREIGN KEY(producto_id, sucursal_id) REFERENCES inventario(producto_id, sucursal_id)
        ON DELETE RESTRICT,
    CHECK ((estado = 'ACTIVA' AND fecha_cierre IS NULL) OR
           (estado != 'ACTIVA' AND fecha_cierre IS NOT NULL))
);
CREATE INDEX idx_reservas_stock_activas ON reservas_stock(producto_id, sucursal_id, estado);

-- La BD por sí misma impide reservar cantidades mayores al stock disponible.
-- BEGIN IMMEDIATE en cada operación asegura serialización entre escritores SQLite.
CREATE TRIGGER trg_reserva_validar_insert
BEFORE INSERT ON reservas_stock
BEGIN
    SELECT CASE WHEN NEW.estado != 'ACTIVA'
        THEN RAISE(ABORT, 'Una reserva nueva debe estar ACTIVA') END;
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM detalles_pedido AS d
        WHERE d.pedido_id = NEW.pedido_id AND d.producto_id = NEW.producto_id
          AND d.cantidad = NEW.cantidad
    ) THEN RAISE(ABORT, 'La reserva debe coincidir con el detalle del pedido') END;
    SELECT CASE WHEN (
        SELECT estado FROM pedidos WHERE id = NEW.pedido_id
    ) IN ('ENTREGADO','CANCELADO')
        THEN RAISE(ABORT, 'No se puede reservar para un pedido cerrado') END;
    SELECT CASE WHEN NEW.cantidad + COALESCE((
        SELECT SUM(cantidad) FROM reservas_stock
        WHERE producto_id = NEW.producto_id AND sucursal_id = NEW.sucursal_id
          AND estado = 'ACTIVA'
    ),0) > COALESCE((
        SELECT cantidad FROM inventario
        WHERE producto_id = NEW.producto_id AND sucursal_id = NEW.sucursal_id
    ),0) THEN RAISE(ABORT, 'Stock insuficiente para reservar') END;
END;

-- Reservas inmutables excepto transición final ACTIVA -> CONSUMIDA/LIBERADA.
CREATE TRIGGER trg_reserva_validar_update
BEFORE UPDATE ON reservas_stock
BEGIN
    SELECT CASE WHEN
        OLD.estado != 'ACTIVA' OR NEW.estado NOT IN ('CONSUMIDA','LIBERADA')
        OR NEW.pedido_id != OLD.pedido_id OR NEW.producto_id != OLD.producto_id
        OR NEW.sucursal_id != OLD.sucursal_id OR NEW.cantidad != OLD.cantidad
        OR NEW.fecha_creacion != OLD.fecha_creacion
        OR NEW.fecha_vencimiento IS NOT OLD.fecha_vencimiento
        OR NEW.fecha_cierre IS NULL
    THEN RAISE(ABORT, 'Transición o modificación de reserva no permitida') END;
END;

CREATE TRIGGER trg_reserva_no_borrar
BEFORE DELETE ON reservas_stock
BEGIN
    SELECT RAISE(ABORT, 'No borrar reservas: conservar trazabilidad');
END;

-- Consumo confirmado: descuenta stock exactamente una vez.
CREATE TRIGGER trg_reserva_consumida
AFTER UPDATE OF estado ON reservas_stock
WHEN OLD.estado = 'ACTIVA' AND NEW.estado = 'CONSUMIDA'
BEGIN
    UPDATE inventario SET cantidad = cantidad - NEW.cantidad
    WHERE producto_id = NEW.producto_id AND sucursal_id = NEW.sucursal_id;
END;

-- No permite reducir inventario por debajo de reservas activas de otros pedidos.
CREATE TRIGGER trg_inventario_proteger_reservas
BEFORE UPDATE OF cantidad ON inventario
WHEN NEW.cantidad < COALESCE((
    SELECT SUM(cantidad) FROM reservas_stock
    WHERE producto_id = NEW.producto_id AND sucursal_id = NEW.sucursal_id
      AND estado = 'ACTIVA'
),0)
BEGIN
    SELECT RAISE(ABORT, 'El stock no puede ser menor a lo reservado');
END;

-- Bloqueo de cambios al detalle ya reservado, incluso después del consumo.
CREATE TRIGGER trg_detalle_reservado_inmutable
BEFORE UPDATE ON detalles_pedido
WHEN EXISTS (SELECT 1 FROM reservas_stock AS r
             WHERE r.pedido_id = OLD.pedido_id AND r.producto_id = OLD.producto_id)
BEGIN
    SELECT RAISE(ABORT, 'No cambiar un detalle que tiene reserva');
END;
