# Diccionario de datos v6

Generado con `python -m scripts.generar_diccionario` desde una base temporal migrada y el módulo de pedidos inicializado. No contiene datos de clientes ni una copia de la base operativa.

[Modelo y reglas](MODELO_DATOS.md). `NN` refleja la declaración NOT NULL de SQLite; las claves primarias tienen además su semántica propia. Los CHECK, índices parciales y triggers se consultan en las migraciones.

**20 tablas**, `application_id=1229867841`, `user_version=6`.

## `catalogo_comercial`

Marca, presentación, imagen, precios en céntimos, máximo y fuente.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `producto_id` | INTEGER | 1 | No | — |
| `marca` | TEXT | 0 | Sí | — |
| `orden` | INTEGER | 0 | Sí | 1000 |
| `presentacion` | TEXT | 0 | Sí | — |
| `descripcion` | TEXT | 0 | Sí | — |
| `imagen` | TEXT | 0 | Sí | — |
| `precio_centimos` | INTEGER | 0 | Sí | — |
| `precio_lista_centimos` | INTEGER | 0 | Sí | — |
| `maximo` | INTEGER | 0 | Sí | 10 |
| `fuente` | TEXT | 0 | Sí | — |
| `fecha_fuente` | TEXT | 0 | Sí | — |

Claves foráneas:
- (producto_id) → productos(id); ON DELETE RESTRICT.

## `categorias`

Clasificación del catálogo.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `codigo` | TEXT | 0 | Sí | — |
| `nombre` | TEXT | 0 | Sí | — |

## `control_reservas`

Asignación vigente, límite y aceptación; control de generación para evitar acciones obsoletas.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `pedido_id` | INTEGER | 1 | No | — |
| `asignacion_id` | INTEGER | 0 | Sí | — |
| `fecha_limite` | TEXT | 0 | No | — |
| `aceptada_en` | TEXT | 0 | No | — |

Claves foráneas:
- (asignacion_id) → historial_asignaciones(id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `detalles_pedido`

Cantidad solicitada por producto; una línea por pedido/producto.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `producto_id` | INTEGER | 0 | Sí | — |
| `cantidad` | INTEGER | 0 | Sí | — |

Claves foráneas:
- (producto_id) → productos(id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `entregas`

Una entrega por pedido, repartidor, estado y fechas.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `repartidor_id` | INTEGER | 0 | Sí | — |
| `estado` | TEXT | 0 | Sí | 'ASIGNADA' |
| `fecha_asignacion` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |
| `fecha_salida` | TEXT | 0 | No | — |
| `fecha_entrega` | TEXT | 0 | No | — |
| `observaciones` | TEXT | 0 | No | — |

Claves foráneas:
- (repartidor_id) → repartidores(id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `historial_asignaciones`

Intentos inmutables de asignación, causa, origen/destino, UUID y actor.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `sucursal_origen_id` | INTEGER | 0 | No | — |
| `sucursal_destino_id` | INTEGER | 0 | No | — |
| `asignacion_anterior_id` | INTEGER | 0 | No | — |
| `causa` | TEXT | 0 | Sí | — |
| `observacion` | TEXT | 0 | Sí | — |
| `incidencia_id` | INTEGER | 0 | No | — |
| `solicitud_id` | TEXT | 0 | No | — |
| `actor_rol` | TEXT | 0 | Sí | — |
| `actor_id` | INTEGER | 0 | No | — |
| `fecha` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |

Claves foráneas:
- (incidencia_id) → incidencias_pedido(id); ON DELETE RESTRICT.
- (asignacion_anterior_id) → historial_asignaciones(id); ON DELETE RESTRICT.
- (sucursal_destino_id) → sucursales(id); ON DELETE RESTRICT.
- (sucursal_origen_id) → sucursales(id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `historial_estados`

Historial inmutable generado por cambios de estado.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `estado_anterior` | TEXT | 0 | No | — |
| `estado_nuevo` | TEXT | 0 | Sí | — |
| `fecha_cambio` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |
| `observacion` | TEXT | 0 | No | — |

Claves foráneas:
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `incidencias_pedido`

Problema, rol reportante y flujo ABIERTA → EN_REVISION → RESUELTA.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `categoria` | TEXT | 0 | Sí | — |
| `descripcion` | TEXT | 0 | Sí | — |
| `reportado_por_rol` | TEXT | 0 | Sí | — |
| `reportado_por_id` | INTEGER | 0 | No | — |
| `estado` | TEXT | 0 | Sí | 'ABIERTA' |
| `resolucion` | TEXT | 0 | No | — |
| `atendido_por_rol` | TEXT | 0 | No | — |
| `atendido_por_id` | INTEGER | 0 | No | — |
| `fecha_creacion` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |
| `fecha_actualizacion` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |
| `fecha_resolucion` | TEXT | 0 | No | — |

Claves foráneas:
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `inventario`

Saldo físico del par producto/sucursal; disponible se calcula restando reservas activas.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `producto_id` | INTEGER | 1 | Sí | — |
| `sucursal_id` | INTEGER | 2 | Sí | — |
| `cantidad` | INTEGER | 0 | Sí | — |

Claves foráneas:
- (sucursal_id) → sucursales(id); ON DELETE RESTRICT.
- (producto_id) → productos(id); ON DELETE RESTRICT.

## `movimientos_inventario`

Apertura, entrada, ajuste o salida; saldos, variación, motivo y actor inmutables.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `producto_id` | INTEGER | 0 | Sí | — |
| `sucursal_id` | INTEGER | 0 | Sí | — |
| `tipo` | TEXT | 0 | Sí | — |
| `cantidad_anterior` | INTEGER | 0 | Sí | — |
| `cantidad_nueva` | INTEGER | 0 | Sí | — |
| `variacion` | INTEGER | 0 | Sí | — |
| `motivo` | TEXT | 0 | Sí | — |
| `solicitud_id` | TEXT | 0 | No | — |
| `pedido_id` | INTEGER | 0 | No | — |
| `reserva_id` | INTEGER | 0 | No | — |
| `actor_rol` | TEXT | 0 | Sí | — |
| `actor_id` | INTEGER | 0 | No | — |
| `fecha` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |

Claves foráneas:
- (producto_id, sucursal_id) → inventario(producto_id, sucursal_id); ON DELETE RESTRICT.
- (reserva_id) → reservas_stock(id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `pedidos`

Código privado, sucursal vigente y estado operativo del pedido.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `codigo` | TEXT | 0 | Sí | — |
| `sucursal_id` | INTEGER | 0 | Sí | — |
| `estado` | TEXT | 0 | Sí | 'REGISTRADO' |
| `fecha_creacion` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |

Claves foráneas:
- (sucursal_id) → sucursales(id); ON DELETE RESTRICT.

## `pedidos_comerciales`

Contacto, dirección, distrito, cotización y totales confirmados; inmutable.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `pedido_id` | INTEGER | 1 | No | — |
| `cotizacion_id` | TEXT | 0 | Sí | — |
| `telefono` | TEXT | 0 | Sí | — |
| `direccion` | TEXT | 0 | Sí | — |
| `distrito` | TEXT | 0 | Sí | — |
| `subtotal_centimos` | INTEGER | 0 | Sí | — |
| `envio_centimos` | INTEGER | 0 | Sí | — |
| `total_centimos` | INTEGER | 0 | Sí | — |
| `moneda` | TEXT | 0 | Sí | 'PEN' |
| `metodo_pago` | TEXT | 0 | Sí | 'AL_RECIBIR' |

Claves foráneas:
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `politica_reservas`

Única configuración del plazo de futuras asignaciones (1–1440 minutos).

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `plazo_minutos` | INTEGER | 0 | Sí | — |

## `precios_pedido`

Cantidad y precio unitario aceptados por línea; inmutable.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `pedido_id` | INTEGER | 1 | Sí | — |
| `producto_id` | INTEGER | 2 | Sí | — |
| `cantidad` | INTEGER | 0 | Sí | — |
| `precio_unitario_centimos` | INTEGER | 0 | Sí | — |

Claves foráneas:
- (pedido_id, producto_id) → detalles_pedido(pedido_id, producto_id); ON DELETE RESTRICT.

## `productos`

Identidad y categoría del producto.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `codigo` | TEXT | 0 | Sí | — |
| `nombre` | TEXT | 0 | Sí | — |
| `categoria_id` | INTEGER | 0 | Sí | — |

Claves foráneas:
- (categoria_id) → categorias(id); ON DELETE RESTRICT.

## `repartidores`

Identidad operativa y disponibilidad del repartidor; no es cuenta autenticada.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `codigo` | TEXT | 0 | Sí | — |
| `nombre` | TEXT | 0 | Sí | — |
| `activo` | INTEGER | 0 | Sí | 1 |

## `reservas_stock`

Intentos históricos de reserva. Solo una ACTIVA/CONSUMIDA por línea; LIBERADA se conserva.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `pedido_id` | INTEGER | 0 | Sí | — |
| `producto_id` | INTEGER | 0 | Sí | — |
| `sucursal_id` | INTEGER | 0 | Sí | — |
| `cantidad` | INTEGER | 0 | Sí | — |
| `estado` | TEXT | 0 | Sí | 'ACTIVA' |
| `fecha_creacion` | TEXT | 0 | Sí | strftime('%Y-%m-%dT%H:%M:%fZ','now') |
| `fecha_cierre` | TEXT | 0 | No | — |
| `fecha_vencimiento` | TEXT | 0 | No | — |

Claves foráneas:
- (producto_id, sucursal_id) → inventario(producto_id, sucursal_id); ON DELETE RESTRICT.
- (pedido_id, producto_id) → detalles_pedido(pedido_id, producto_id); ON DELETE RESTRICT.
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `s2_capacidades`

Límite explícito de preparación por sucursal; cero deshabilita nuevas asignaciones.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `sucursal_id` | INTEGER | 1 | No | — |
| `capacidad_maxima` | INTEGER | 0 | Sí | — |

Claves foráneas:
- (sucursal_id) → sucursales(id); ON DELETE RESTRICT.

## `s2_solicitudes`

Nombre de cliente, coordenadas usadas y distancia de asignación.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `pedido_id` | INTEGER | 1 | No | — |
| `cliente` | TEXT | 0 | Sí | — |
| `latitud` | REAL | 0 | Sí | — |
| `longitud` | REAL | 0 | Sí | — |
| `distancia_km` | REAL | 0 | Sí | — |

Claves foráneas:
- (pedido_id) → pedidos(id); ON DELETE RESTRICT.

## `sucursales`

Locales de atención y coordenadas geográficas.

| Campo | Tipo | PK (orden) | NN | Predeterminado SQL |
|---|---|---:|---|---|
| `id` | INTEGER | 1 | No | — |
| `codigo` | TEXT | 0 | Sí | — |
| `nombre` | TEXT | 0 | Sí | — |
| `latitud` | REAL | 0 | Sí | — |
| `longitud` | REAL | 0 | Sí | — |

