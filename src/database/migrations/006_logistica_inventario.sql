-- HU02 / HU03 / HU09 / HU14. Conserva reservas cerradas al reasignar.
-- No se desactivan claves foráneas ni se descuentan existencias al migrar.
DROP TRIGGER trg_reserva_validar_insert;
DROP TRIGGER trg_reserva_validar_update;
DROP TRIGGER trg_reserva_no_borrar;
DROP TRIGGER trg_reserva_consumida;
DROP TRIGGER trg_inventario_proteger_reservas;
DROP TRIGGER trg_detalle_reservado_inmutable;

CREATE TABLE reservas_stock_v6 (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    producto_id INTEGER NOT NULL,
    sucursal_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad)='integer' AND cantidad>0),
    estado TEXT NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA','CONSUMIDA','LIBERADA')),
    fecha_creacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    fecha_cierre TEXT,
    fecha_vencimiento TEXT,
    FOREIGN KEY(pedido_id,producto_id) REFERENCES detalles_pedido(pedido_id,producto_id) ON DELETE RESTRICT,
    FOREIGN KEY(producto_id,sucursal_id) REFERENCES inventario(producto_id,sucursal_id) ON DELETE RESTRICT,
    CHECK ((estado='ACTIVA' AND fecha_cierre IS NULL) OR (estado!='ACTIVA' AND fecha_cierre IS NOT NULL))
);
INSERT INTO reservas_stock_v6 SELECT * FROM reservas_stock;
DROP TABLE reservas_stock;
ALTER TABLE reservas_stock_v6 RENAME TO reservas_stock;
-- Una línea puede tener reservas históricas liberadas, pero solo una vigente/consumida.
CREATE UNIQUE INDEX idx_reserva_vigente ON reservas_stock(pedido_id,producto_id) WHERE estado!='LIBERADA';
CREATE INDEX idx_reservas_stock_activas ON reservas_stock(producto_id,sucursal_id,estado);
CREATE INDEX idx_reservas_pedido ON reservas_stock(pedido_id,producto_id,id);

CREATE TABLE politica_reservas (
    id INTEGER PRIMARY KEY CHECK (id=1),
    plazo_minutos INTEGER NOT NULL CHECK (typeof(plazo_minutos)='integer' AND plazo_minutos BETWEEN 1 AND 1440)
);
INSERT INTO politica_reservas VALUES(1,15);

CREATE TABLE historial_asignaciones (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    sucursal_origen_id INTEGER REFERENCES sucursales(id) ON DELETE RESTRICT,
    sucursal_destino_id INTEGER REFERENCES sucursales(id) ON DELETE RESTRICT,
    asignacion_anterior_id INTEGER UNIQUE REFERENCES historial_asignaciones(id) ON DELETE RESTRICT,
    causa TEXT NOT NULL CHECK (causa IN ('INICIAL','MIGRACION','RECHAZO_SUCURSAL','PLAZO_AGOTADO')),
    observacion TEXT NOT NULL,
    incidencia_id INTEGER REFERENCES incidencias_pedido(id) ON DELETE RESTRICT,
    solicitud_id TEXT UNIQUE,
    actor_rol TEXT NOT NULL CHECK (actor_rol IN ('SISTEMA','ADMINISTRADOR','PERSONAL_SUCURSAL')),
    actor_id INTEGER,
    fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    CHECK (sucursal_origen_id IS NULL OR sucursal_destino_id IS NULL OR sucursal_origen_id!=sucursal_destino_id)
);
CREATE INDEX idx_asignaciones_pedido ON historial_asignaciones(pedido_id,id);
CREATE TABLE control_reservas (
    pedido_id INTEGER PRIMARY KEY REFERENCES pedidos(id) ON DELETE RESTRICT,
    asignacion_id INTEGER NOT NULL UNIQUE REFERENCES historial_asignaciones(id) ON DELETE RESTRICT,
    fecha_limite TEXT,
    aceptada_en TEXT
);
CREATE INDEX idx_control_vencimiento ON control_reservas(fecha_limite) WHERE aceptada_en IS NULL;

-- Las reservas anteriores a v6 reciben el plazo completo desde la migración.
INSERT INTO historial_asignaciones(pedido_id,sucursal_destino_id,causa,observacion,actor_rol)
    SELECT id,sucursal_id,'MIGRACION','Asignación conservada al actualizar la logística.','SISTEMA' FROM pedidos;
INSERT INTO control_reservas(pedido_id,asignacion_id,fecha_limite,aceptada_en)
    SELECT p.id,h.id,
        CASE WHEN p.estado IN ('REGISTRADO','ASIGNADO')
             THEN strftime('%Y-%m-%dT%H:%M:%fZ','now','+15 minutes') END,
        CASE WHEN p.estado NOT IN ('REGISTRADO','ASIGNADO') THEN strftime('%Y-%m-%dT%H:%M:%fZ','now') END
    FROM pedidos p JOIN historial_asignaciones h ON h.pedido_id=p.id;

CREATE TRIGGER trg_asignacion_inicial AFTER INSERT ON pedidos
BEGIN
    INSERT INTO historial_asignaciones(pedido_id,sucursal_destino_id,causa,observacion,actor_rol)
        VALUES(NEW.id,NEW.sucursal_id,'INICIAL','Sucursal seleccionada por stock, capacidad y distancia.','SISTEMA');
    INSERT INTO control_reservas(pedido_id,asignacion_id,fecha_limite)
        VALUES(NEW.id,last_insert_rowid(),strftime('%Y-%m-%dT%H:%M:%fZ','now',
            '+' || (SELECT plazo_minutos FROM politica_reservas WHERE id=1) || ' minutes'));
END;
CREATE TRIGGER trg_asignacion_no_cambiar BEFORE UPDATE ON historial_asignaciones
BEGIN SELECT RAISE(ABORT,'El historial de asignaciones es inmutable'); END;
CREATE TRIGGER trg_asignacion_no_borrar BEFORE DELETE ON historial_asignaciones
BEGIN SELECT RAISE(ABORT,'El historial de asignaciones es inmutable'); END;
CREATE TRIGGER trg_pedido_reasignacion_validar BEFORE UPDATE OF sucursal_id ON pedidos
WHEN NEW.sucursal_id!=OLD.sucursal_id
BEGIN
    SELECT CASE WHEN OLD.estado NOT IN ('REGISTRADO','ASIGNADO','EN_PREPARACION')
        OR NEW.estado!='ASIGNADO'
        OR EXISTS(SELECT 1 FROM reservas_stock WHERE pedido_id=OLD.id AND estado!='LIBERADA')
        OR NOT EXISTS(SELECT 1 FROM historial_asignaciones h WHERE h.id=(
            SELECT max(id) FROM historial_asignaciones WHERE pedido_id=OLD.id)
            AND h.sucursal_origen_id=OLD.sucursal_id AND h.sucursal_destino_id=NEW.sucursal_id)
    THEN RAISE(ABORT,'Reasignación sin liberación e historial válidos') END;
END;

CREATE TRIGGER trg_reserva_validar_insert BEFORE INSERT ON reservas_stock
BEGIN
    SELECT CASE WHEN NEW.estado!='ACTIVA' OR NOT EXISTS (
        SELECT 1 FROM pedidos p WHERE p.id=NEW.pedido_id AND p.sucursal_id=NEW.sucursal_id
          AND p.estado IN ('REGISTRADO','ASIGNADO'))
        THEN RAISE(ABORT,'La reserva debe pertenecer a la asignación vigente') END;
    SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM detalles_pedido d
        WHERE d.pedido_id=NEW.pedido_id AND d.producto_id=NEW.producto_id AND d.cantidad=NEW.cantidad)
        THEN RAISE(ABORT,'La reserva debe coincidir con el detalle del pedido') END;
    SELECT CASE WHEN NEW.cantidad+COALESCE((SELECT sum(cantidad) FROM reservas_stock
        WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id AND estado='ACTIVA'),0)
        >COALESCE((SELECT cantidad FROM inventario WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id),0)
        THEN RAISE(ABORT,'Stock insuficiente para reservar') END;
END;
CREATE TRIGGER trg_reserva_validar_update BEFORE UPDATE ON reservas_stock
BEGIN
    SELECT CASE WHEN OLD.estado!='ACTIVA' OR NEW.estado NOT IN ('CONSUMIDA','LIBERADA')
        OR NEW.id!=OLD.id OR NEW.pedido_id!=OLD.pedido_id OR NEW.producto_id!=OLD.producto_id
        OR NEW.sucursal_id!=OLD.sucursal_id OR NEW.cantidad!=OLD.cantidad
        OR NEW.fecha_creacion!=OLD.fecha_creacion OR NEW.fecha_vencimiento IS NOT OLD.fecha_vencimiento
        OR NEW.fecha_cierre IS NULL
        THEN RAISE(ABORT,'Transición o modificación de reserva no permitida') END;
END;
CREATE TRIGGER trg_reserva_no_borrar BEFORE DELETE ON reservas_stock
BEGIN SELECT RAISE(ABORT,'No borrar reservas: conservar trazabilidad'); END;
CREATE TRIGGER trg_inventario_proteger_reservas BEFORE UPDATE OF cantidad ON inventario
WHEN NEW.cantidad<COALESCE((SELECT sum(cantidad) FROM reservas_stock
    WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id AND estado='ACTIVA'),0)
BEGIN SELECT RAISE(ABORT,'El stock no puede ser menor a lo reservado'); END;
CREATE TRIGGER trg_detalle_reservado_inmutable BEFORE UPDATE ON detalles_pedido
WHEN EXISTS(SELECT 1 FROM reservas_stock WHERE pedido_id=OLD.pedido_id AND producto_id=OLD.producto_id)
BEGIN SELECT RAISE(ABORT,'No cambiar un detalle que tiene reserva'); END;

CREATE TABLE movimientos_inventario (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER NOT NULL,
    sucursal_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('APERTURA','ENTRADA','AJUSTE','SALIDA_PEDIDO')),
    cantidad_anterior INTEGER NOT NULL CHECK (typeof(cantidad_anterior)='integer' AND cantidad_anterior>=0),
    cantidad_nueva INTEGER NOT NULL CHECK (typeof(cantidad_nueva)='integer' AND cantidad_nueva>=0),
    variacion INTEGER NOT NULL CHECK (variacion=cantidad_nueva-cantidad_anterior),
    motivo TEXT NOT NULL CHECK (length(trim(motivo)) BETWEEN 5 AND 240),
    solicitud_id TEXT UNIQUE,
    pedido_id INTEGER REFERENCES pedidos(id) ON DELETE RESTRICT,
    reserva_id INTEGER UNIQUE REFERENCES reservas_stock(id) ON DELETE RESTRICT,
    actor_rol TEXT NOT NULL CHECK (actor_rol IN ('SISTEMA','ADMINISTRADOR','PERSONAL_SUCURSAL')),
    actor_id INTEGER,
    fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY(producto_id,sucursal_id) REFERENCES inventario(producto_id,sucursal_id) ON DELETE RESTRICT,
    CHECK ((tipo='APERTURA' AND cantidad_anterior=0 AND solicitud_id IS NULL AND pedido_id IS NULL AND reserva_id IS NULL)
        OR (tipo='ENTRADA' AND variacion>0 AND solicitud_id IS NOT NULL AND pedido_id IS NULL AND reserva_id IS NULL)
        OR (tipo='AJUSTE' AND variacion!=0 AND solicitud_id IS NOT NULL AND pedido_id IS NULL AND reserva_id IS NULL)
        OR (tipo='SALIDA_PEDIDO' AND variacion<0 AND solicitud_id IS NULL AND pedido_id IS NOT NULL AND reserva_id IS NOT NULL))
);
CREATE INDEX idx_movimientos_inventario ON movimientos_inventario(producto_id,sucursal_id,id);
INSERT INTO movimientos_inventario(producto_id,sucursal_id,tipo,cantidad_anterior,cantidad_nueva,variacion,motivo,actor_rol)
    SELECT producto_id,sucursal_id,'APERTURA',0,cantidad,cantidad,'Saldo al incorporar el registro de movimientos.','SISTEMA' FROM inventario;

CREATE TRIGGER trg_movimiento_validar BEFORE INSERT ON movimientos_inventario
BEGIN
    SELECT CASE WHEN NEW.tipo='APERTURA' AND (EXISTS(SELECT 1 FROM movimientos_inventario
        WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id)
        OR NEW.cantidad_nueva!=(SELECT cantidad FROM inventario WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id))
        THEN RAISE(ABORT,'El saldo de apertura ya existe o es incoherente') END;
    SELECT CASE WHEN NEW.tipo!='APERTURA' AND NEW.cantidad_anterior!=(
        SELECT cantidad FROM inventario WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id)
        THEN RAISE(ABORT,'El saldo de inventario cambió') END;
    SELECT CASE WHEN NEW.tipo='SALIDA_PEDIDO' AND NOT EXISTS(SELECT 1 FROM reservas_stock r
        WHERE r.id=NEW.reserva_id AND r.estado='CONSUMIDA' AND r.pedido_id=NEW.pedido_id
          AND r.producto_id=NEW.producto_id AND r.sucursal_id=NEW.sucursal_id AND r.cantidad=-NEW.variacion)
        THEN RAISE(ABORT,'La salida debe corresponder a una reserva consumida') END;
END;
CREATE TRIGGER trg_movimiento_aplicar AFTER INSERT ON movimientos_inventario WHEN NEW.tipo!='APERTURA'
BEGIN
    UPDATE inventario SET cantidad=NEW.cantidad_nueva
        WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id;
END;
CREATE TRIGGER trg_movimiento_no_cambiar BEFORE UPDATE ON movimientos_inventario
BEGIN SELECT RAISE(ABORT,'Los movimientos de inventario son inmutables'); END;
CREATE TRIGGER trg_movimiento_no_borrar BEFORE DELETE ON movimientos_inventario
BEGIN SELECT RAISE(ABORT,'Los movimientos de inventario son inmutables'); END;
CREATE TRIGGER trg_inventario_exigir_movimiento BEFORE UPDATE OF cantidad ON inventario
WHEN NEW.cantidad!=OLD.cantidad AND NOT EXISTS(SELECT 1 FROM movimientos_inventario m
    WHERE m.id=(SELECT max(id) FROM movimientos_inventario WHERE producto_id=OLD.producto_id AND sucursal_id=OLD.sucursal_id)
      AND m.cantidad_anterior=OLD.cantidad AND m.cantidad_nueva=NEW.cantidad AND m.tipo!='APERTURA')
BEGIN SELECT RAISE(ABORT,'Registra un movimiento para cambiar el inventario'); END;
CREATE TRIGGER trg_inventario_apertura AFTER INSERT ON inventario
BEGIN
    INSERT INTO movimientos_inventario(producto_id,sucursal_id,tipo,cantidad_anterior,cantidad_nueva,variacion,motivo,actor_rol)
        VALUES(NEW.producto_id,NEW.sucursal_id,'APERTURA',0,NEW.cantidad,NEW.cantidad,'Saldo inicial de producto en sucursal.','SISTEMA');
END;
CREATE TRIGGER trg_reserva_consumida AFTER UPDATE OF estado ON reservas_stock
WHEN OLD.estado='ACTIVA' AND NEW.estado='CONSUMIDA'
BEGIN
    INSERT INTO movimientos_inventario(producto_id,sucursal_id,tipo,cantidad_anterior,cantidad_nueva,variacion,
        motivo,pedido_id,reserva_id,actor_rol)
        SELECT NEW.producto_id,NEW.sucursal_id,'SALIDA_PEDIDO',cantidad,cantidad-NEW.cantidad,-NEW.cantidad,
            'Salida al iniciar el reparto del pedido.',NEW.pedido_id,NEW.id,'SISTEMA'
        FROM inventario WHERE producto_id=NEW.producto_id AND sucursal_id=NEW.sucursal_id;
END;
