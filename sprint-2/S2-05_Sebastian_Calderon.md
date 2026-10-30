# S2-05 — Integración y pruebas de pedidos

Issue [#12](https://github.com/seale-code/Ingenieria-de-software/issues/12).

La interfaz pública de Anderson (`iniciar_modulo`, `configurar_capacidad`,
`registrar_pedido`, `obtener_pedido` y CLI) ahora reconoce el esquema de Josué v2/v3.
El puente `src/backend/pedidos_integracion.py` usa directamente las reglas de César
y guarda pedidos, detalles y reservas en las tablas oficiales. La selección y la
reserva se ejecutan dentro del mismo `BEGIN IMMEDIATE`, evitando sobreventa y
exceso de capacidad entre las conexiones probadas.

## Demostración con base nueva y datos ficticios

Python 3.10+, sin paquetes adicionales para esta demostración:

```bash
python -m src.database init --demo --db .test-tmp/s2-demo.sqlite3
python -m src.database.migrate_josue --db .test-tmp/s2-demo.sqlite3 --hasta 2
python -m src.backend.pedidos_s2_cli --db .test-tmp/s2-demo.sqlite3 init
python -m src.backend.pedidos_s2_cli --db .test-tmp/s2-demo.sqlite3 capacidad --sucursal DEMO-NORTE --max-pedidos 10
python -m src.backend.pedidos_s2_cli --db .test-tmp/s2-demo.sqlite3 registrar --cliente "Cliente ficticio" --lat -12 --lon -77.05 --item DEMO-A:2
python -m src.backend.pedidos_s2_cli --db .test-tmp/s2-demo.sqlite3 consultar --pedido 1
```

El ID de la última línea debe ser el que devuelve registrar; 1 supone base nueva.
Para reiniciar una demostración, usar otro nombre de base; no borrar datos ajenos.

## Contrato para conectar el formulario

`registrar_pedido` recibe `cliente` (texto de demostración, no una cuenta),
`latitud`, `longitud` y `items`: lista de objetos `producto_codigo` y `cantidad`.
Cantidad: entero positivo, máximo 10000 acumulado por producto; hasta 100 líneas.
Agrupa productos repetidos. Devuelve `pedido_id`, `estado`, `sucursal_codigo`,
`sucursal_nombre`, `distancia_km`, `motivo`, `items` y, en modo oficial, `motivo_codigo`.

- ASIGNADO: ID persistido, detalle completo y reserva ACTIVA para cada producto.
- SIN_ASIGNAR: `pedido_id=None`, motivo claro y ninguna escritura parcial.
  El esquema oficial exige una sucursal y no contempla pedidos sin asignación.
- Datos inválidos: `DatosInvalidos`; el CLI informa el error y sale con código 2.
- Módulo sin inicializar o datos provisionales pendientes: `ModuloNoInicializado`.
- Error al persistir: rollback completo; el adaptador HTTP futuro deberá mapearlo
  a un error recuperable sin exponer detalles SQL.

Capacidad sin configurar: 10, valor definido en las reglas de César. Configurar 0
deshabilita una sucursal. El cálculo resta reservas oficiales ACTIVAS del stock físico
antes de evaluar elegibilidad. Reservar no descuenta inventario: el trigger de Josué
lo descuenta una sola vez al consumir. El detalle indica reserva activa, no historial.

## Compatibilidad y límites

Las bases v1 conservan el módulo provisional de Anderson; no acreditan la integración
oficial. Si se migró una base que contiene `s2_pedidos`, el módulo exige conciliar
esos pedidos antes de habilitar escrituras oficiales. No se migra ni se borra ese
historial automáticamente: el modelo provisional ya descontó inventario, por lo que
una copia directa causaría doble descuento. Una base v1 sin pedidos puede migrarse
con la herramienta de Josué e inicializar este complemento sin pérdida de inventario.

El complemento solo agrega configuración de capacidad y metadata de solicitud,
referenciando el pedido oficial. No cambia `user_version` ni las migraciones del equipo.

Pendientes del sprint: formulario/resumen/confirmación #20, conexión HTTP de pedidos,
cuenta y permisos de HU04, duración/liberación de reservas, avisos a la sucursal y
reglas de reasignación. El catálogo S1 muestra stock físico; antes de habilitar compra
se debe mostrar o explicar el disponible descontando reservas. Esta entrega valida
el servicio y la consola; el flujo web de compra aún requiere esos componentes.

[Casos de prueba](../docs/05-pruebas/S2-05-casos-prueba-pedidos.md) ·
[Resultados y defectos](../docs/06-evidencias/2026-10-29_integracion-sprint-2.md).
