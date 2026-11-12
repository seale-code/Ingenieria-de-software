-- S3-04 / Issue #22: soporte e incidencias asociadas a pedidos.
-- Requiere esquema v3. Aplicar con: python -m src.database.migrate_josue --hasta 4

CREATE TABLE incidencias_pedido (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE RESTRICT,
    categoria TEXT NOT NULL CHECK (categoria IN (
        'RETRASO', 'PRODUCTO_FALTANTE', 'PRODUCTO_DANADO',
        'DIRECCION_INCORRECTA', 'CLIENTE_AUSENTE', 'OTRO'
    )),
    descripcion TEXT NOT NULL
        CHECK (length(trim(descripcion)) BETWEEN 1 AND 2000),
    reportado_por_rol TEXT NOT NULL CHECK (reportado_por_rol IN (
        'PERSONAL_SUCURSAL', 'REPARTIDOR', 'ASESOR', 'ADMINISTRADOR'
    )),
    reportado_por_id INTEGER,
    estado TEXT NOT NULL DEFAULT 'ABIERTA'
        CHECK (estado IN ('ABIERTA', 'EN_REVISION', 'RESUELTA')),
    resolucion TEXT,
    atendido_por_rol TEXT CHECK (
        atendido_por_rol IS NULL OR atendido_por_rol IN ('ASESOR', 'ADMINISTRADOR')
    ),
    atendido_por_id INTEGER,
    fecha_creacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    fecha_actualizacion TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    fecha_resolucion TEXT,
    CHECK (
        (estado = 'ABIERTA' AND resolucion IS NULL AND fecha_resolucion IS NULL
            AND atendido_por_rol IS NULL)
        OR
        (estado = 'EN_REVISION' AND resolucion IS NULL AND fecha_resolucion IS NULL
            AND atendido_por_rol IN ('ASESOR', 'ADMINISTRADOR'))
        OR
        (estado = 'RESUELTA' AND length(trim(COALESCE(resolucion, ''))) > 0
            AND fecha_resolucion IS NOT NULL
            AND atendido_por_rol IN ('ASESOR', 'ADMINISTRADOR'))
    )
);

CREATE INDEX idx_incidencias_pedido_estado
    ON incidencias_pedido(pedido_id, estado, fecha_creacion);

CREATE INDEX idx_incidencias_estado_fecha
    ON incidencias_pedido(estado, fecha_creacion);

-- Mantengo la trazabilidad: las incidencias no se eliminan físicamente.
CREATE TRIGGER trg_incidencias_no_borrar
BEFORE DELETE ON incidencias_pedido
BEGIN
    SELECT RAISE(ABORT, 'No borrar incidencias: conservar trazabilidad');
END;

-- La incidencia solo avanza ABIERTA -> EN_REVISION -> RESUELTA.
CREATE TRIGGER trg_incidencias_transicion
BEFORE UPDATE OF estado ON incidencias_pedido
WHEN NEW.estado != OLD.estado
BEGIN
    SELECT CASE WHEN NOT (
        (OLD.estado = 'ABIERTA' AND NEW.estado = 'EN_REVISION')
        OR
        (OLD.estado = 'EN_REVISION' AND NEW.estado = 'RESUELTA')
    ) THEN RAISE(ABORT, 'Transicion de incidencia no permitida') END;
END;
