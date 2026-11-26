# Requisitos trazables al alcance actual

[← Documentación](../README.md) · [Alcance](ALCANCE_Y_OBJETIVOS.md) · [Product Backlog](../07-scrum/PRODUCT_BACKLOG.md)

## Base y control

Revisión DOC-01 (#60), base `53b6ff85a4904c6c3f1beb6c73ab4601c4b14886`. Se conservan los IDs de planificación, el PDF original y los requisitos históricos. La cobertura técnica no equivale a aceptación del equipo. Los requisitos EXT son desgloses propuestos para revisión, no nuevos compromisos de sprint.

## Actores

Cliente web sin cuenta; operador del panel con clave compartida; personal de sucursal, administrador y repartidor representados en servicios y flujo operativo (sin afirmar cuentas individuales).

## Requisitos funcionales originales

| ID | Requisito original | Fuente | Plan original | Cobertura observada |
|---|---|---|---|---|
| RF-S1-01 | Consultar catálogo y buscar por nombre, informando si no hay coincidencias. | HU01 / PBI-01; plan S1 | Tareas #5, #4, #7, #13, #14, #11.  | Búsqueda por nombre/marca y catálogo visual: app.py, catalogo.js. |
| RF-S1-02 | Filtrar por categoría, sucursal y solo productos con stock; combinar con búsqueda. | Descomposición del plan S1, apoyo a HU01 | #1, #2, #8.  | Filtros combinados: app.py y catalogo.js. |
| RF-S1-03 | Consultar disponibilidad del producto por sucursal. | HU01 / PBI-01 | #10 y tareas de interfaz e integración.  | Stock efectivo por sucursal: app.py, database.py. |
| RF-S1-04 | Mostrar primero las sucursales más cercanas con disponibilidad. | HU01, criterio 2 | Falta tarea específica y definición de ubicación/distancia.  | Pendiente: database.py ordena por código; distancia solo en asignación. |
| RF-S1-05 | Modelar Producto, Sucursal e Inventario y cargar datos ficticios. | Plan S1; base de HU14 | #6, #3; cobertura parcial de HU14.  | Modelo y migraciones implementados; datos ficticios. |
| RF-S2-01 | Registrar y confirmar un pedido con sus productos y cantidades. | HU04 / PBI-04 | #20, #18, #12; refinar cuenta, carrito y plataforma.  | Carrito, cotización y confirmación web sin cuenta: tienda.js, comercio.py, pedidos_web.py. |
| RF-S2-02 | Reservar stock y liberarlo al vencer el plazo; notificar a la sucursal. | HU02 / PBI-02 | #21, #18; expiración y notificación requieren detalle.  | Adaptado a plazo de aceptación, bandeja y liberación/reasignación: logistica.py, vencimientos.py. |
| RF-S2-03 | Asignar sucursal considerando stock, distancia y capacidad; gestionar falta de alternativa. | HU03 y HU15 | #9, #18, #12; acordar reglas y desempates.  | Asignación y alternativa: asignacion_sucursal.py, logistica.py. |
| RF-S3-01 | Gestionar preparación y cambios de estado autorizados. | Plan S3; HU05 y HU15 | #16, #22.  | Preparación autorizada: preparacion_pedidos.py, operaciones_demo.py. |
| RF-S3-02 | Mostrar estado e historial e informar cambios al cliente. | HU05 / PBI-05 | #15, #19, #22; notificaciones por detallar.  | Seguimiento por código e historial: seguimiento.py; sin avisos activos ni recojo. |
| RF-S3-03 | Registrar repartidor, entrega y confirmación final. | HU15 / PBI-15 | #19, #22, #17.  | Registro de repartidor, despacho y entrega: reparto_integrado.py, operaciones_demo.py. |
| RF-S3-04 | Registrar incidencias y soporte básico asociado al pedido. | Plan S3; relación parcial con HU11 | #22; no cubre todavía un chat completo.  | Incidencias internas: soporte_pedidos_s3.py; sin chat. |

## Desglose de ampliaciones implementadas (propuesto)

| ID | Requisito | HU relacionada | Código de respaldo (src) |
|---|---|---|---|
| RF-EXT-01 | Catálogo visual, marca, presentación, precio y ordenamiento por nombre/precio. | HU01/HU07 | catalogo.js, app.py, comercio.py |
| RF-EXT-02 | Cotizar carrito en servidor, mostrar subtotal, envío y total en PEN; validar cantidades y conservar importes confirmados; pago al recibir. | HU04 | comercio.py, pedidos_web.py, tienda.js |
| RF-EXT-03 | Aceptar asignación al iniciar preparación; plazo inicial configurable de 15 minutos; reasignar sin repetir sucursales intentadas o cancelar y liberar reservas. | HU02/HU03/HU09 | logistica.py, vencimientos.py |
| RF-EXT-04 | Consultar inventario físico, reservado y disponible; registrar ingreso, ajuste y salida al despacho con historial e idempotencia. | HU14/HU15 | inventario.py, reparto_integrado.py |
| RF-EXT-05 | Autorizar API operativa mediante clave compartida, sesión y token CSRF para escrituras; no equivale a cuentas individuales. | HU14/HU15; requisito transversal | operaciones_demo.py, app.py |
| RF-EXT-06 | Mostrar seguimiento por código privado, sucursal y cambios de asignación sin contactos ni motivos internos. | HU05/HU09/HU15 | seguimiento.py |
| RF-EXT-07 | Registrar y atender incidencias operativas vinculadas a pedidos, incluyendo resultado de falta de atención. | HU09/HU11 | soporte_pedidos_s3.py, operaciones_demo.py |

## Requisitos no funcionales y verificación

| ID propuesto | Requisito | Evidencia o validación pendiente |
|---|---|---|
| RNF-01 | Mostrar mensajes claros de carga, vacío, errores y confirmación. | catalogo.js, pedido.js; validar usabilidad con usuarios. |
| RNF-02 | Permitir uso web en pantallas pequeñas y de escritorio. | Evidencias Chromium, incluyendo 320/390 px; no certifica accesibilidad. |
| RNF-03 | Proteger escrituras administrativas mediante sesión y CSRF; rechazar origen distinto cuando se informa. | operaciones_demo.py; auditoría DOC-09 pendiente. |
| RNF-04 | No revelar contactos ni motivos internos en seguimiento público; exigir código privado. | seguimiento.py; auditoría pendiente. |
| RNF-05 | No permitir stock negativo ni reservas superiores al físico; mantener consistencia ante concurrencia. | inventario.py, logistica.py, pruebas de logística. |
| RNF-06 | Conservar pedidos, importes, inventario y movimientos al reiniciar. | SQLite y migraciones; evidencia de reinicio. |
| RNF-07 | Evitar duplicación de salidas y operaciones reintentadas. | UUID, transacciones y pruebas de logística. |
| RNF-08 | Mantener capas frontend, backend y persistencia separadas. | src/frontend, src/backend, src/database. |
| RNF-09 | Ejecutar en entorno Python compatible con dependencias fijadas. | README indica 3.10+; evidencia registrada en 3.12, otras versiones por validar. |
| RNF-10 | Registrar transiciones, movimientos y reasignaciones. | Migraciones y servicios de logística. |
| RNF-11 | Permitir pruebas reproducibles con bases temporales. | unittest y Playwright. |
| RNF-12 | Definir y medir tiempos de respuesta antes de aceptar rendimiento. | Pendiente de umbral y medición. |

## Brechas y límites

Ver [historias actualizadas](../02-historias-usuario/HISTORIAS_ACTUALIZADAS.md) para cobertura por criterio. No se implementan cuentas de cliente, chat, alertas de reposición, recojo, integración comercial real ni comparación de precios por sucursal. No confundir controles existentes con una auditoría de seguridad aprobada.

## Validación

[Casos de prueba](../05-pruebas/CASOS_DE_PRUEBA.md) · [Reglas operativas](../LOGISTICA_SUCURSALES.md) · [Evidencia 16/11/2026](../06-evidencias/2026-11-16_logistica-sucursales.md): 322 pruebas Python/API y 44 Chromium según registros existentes. No se ejecutaron de nuevo en esta revisión.
