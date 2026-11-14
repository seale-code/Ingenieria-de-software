-- Información comercial y valores del pedido conservados al confirmar.
CREATE TABLE catalogo_comercial (
    producto_id INTEGER PRIMARY KEY REFERENCES productos(id) ON DELETE RESTRICT,
    marca TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 1000,
    presentacion TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    imagen TEXT NOT NULL,
    precio_centimos INTEGER NOT NULL CHECK(typeof(precio_centimos)='integer' AND precio_centimos>0),
    precio_lista_centimos INTEGER NOT NULL CHECK(typeof(precio_lista_centimos)='integer' AND precio_lista_centimos>=precio_centimos),
    maximo INTEGER NOT NULL DEFAULT 10 CHECK(maximo BETWEEN 1 AND 100),
    fuente TEXT NOT NULL,
    fecha_fuente TEXT NOT NULL
);

CREATE TABLE pedidos_comerciales (
    pedido_id INTEGER PRIMARY KEY REFERENCES pedidos(id) ON DELETE RESTRICT,
    cotizacion_id TEXT NOT NULL,
    telefono TEXT NOT NULL,
    direccion TEXT NOT NULL,
    distrito TEXT NOT NULL,
    subtotal_centimos INTEGER NOT NULL CHECK(typeof(subtotal_centimos)='integer' AND subtotal_centimos>0),
    envio_centimos INTEGER NOT NULL CHECK(typeof(envio_centimos)='integer' AND envio_centimos>=0),
    total_centimos INTEGER NOT NULL CHECK(total_centimos=subtotal_centimos+envio_centimos),
    moneda TEXT NOT NULL DEFAULT 'PEN' CHECK(moneda='PEN'),
    metodo_pago TEXT NOT NULL DEFAULT 'AL_RECIBIR' CHECK(metodo_pago='AL_RECIBIR')
);

CREATE TABLE precios_pedido (
    pedido_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK(typeof(cantidad)='integer' AND cantidad>0),
    precio_unitario_centimos INTEGER NOT NULL CHECK(typeof(precio_unitario_centimos)='integer' AND precio_unitario_centimos>0),
    PRIMARY KEY(pedido_id,producto_id),
    FOREIGN KEY(pedido_id,producto_id) REFERENCES detalles_pedido(pedido_id,producto_id) ON DELETE RESTRICT
);

CREATE TRIGGER trg_precios_pedido_inmutables BEFORE UPDATE ON precios_pedido
BEGIN SELECT RAISE(ABORT,'Conservar los precios confirmados del pedido'); END;
CREATE TRIGGER trg_precios_pedido_no_borrar BEFORE DELETE ON precios_pedido
BEGIN SELECT RAISE(ABORT,'Conservar los precios confirmados del pedido'); END;
CREATE TRIGGER trg_pedido_comercial_inmutable BEFORE UPDATE ON pedidos_comerciales
BEGIN SELECT RAISE(ABORT,'Conservar los importes confirmados del pedido'); END;
CREATE TRIGGER trg_pedido_comercial_no_borrar BEFORE DELETE ON pedidos_comerciales
BEGIN SELECT RAISE(ABORT,'Conservar los importes confirmados del pedido'); END;
