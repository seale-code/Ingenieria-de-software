# Requisitos trazables al alcance actual

[← Documentación](../README.md) · [Alcance](ALCANCE_Y_OBJETIVOS.md) · [Product Backlog](../07-scrum/PRODUCT_BACKLOG.md)

## Criterio de uso

Este documento organiza lo ya previsto en historias y sprints. La base de RF-S1-05 está implementada y probada, pendiente de revisión del equipo; los flujos integrados restantes siguen pendientes. Los IDs RF-S1/S2/S3 identifican esta versión y no reutilizan los RF-01–RF-12 del [documento histórico](../00-historico/01-requisitos/REQUISITOS.md).

Los criterios completos del [PDF HU01–HU15](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf) prevalecen sobre estos resúmenes. PBI y prioridad detallados están en el backlog.

## Actores

| Actor | Participación prevista |
|---|---|
| Cliente | Buscar, consultar disponibilidad, solicitar pedido y consultar estado. |
| Personal de sucursal / almacén | Preparar pedidos y gestionar inventario según permisos por definir. |
| Repartidor | Participar en la entrega, según el plan S3. |
| Administrador / asesor | Gestión autorizada y soporte; alcance por refinar. |

## Requisitos funcionales por sprint

| ID | Requisito | Fuente | Cobertura de planificación |
|---|---|---|---|
| RF-S1-01 | Consultar catálogo y buscar por nombre, informando si no hay coincidencias. | HU01 / PBI-01; plan S1 | Tareas #5, #4, #7, #13, #14, #11. |
| RF-S1-02 | Filtrar por categoría, sucursal y solo productos con stock; combinar con búsqueda. | Descomposición del plan S1, apoyo a HU01 | #1, #2, #8. |
| RF-S1-03 | Consultar disponibilidad del producto por sucursal. | HU01 / PBI-01 | #10 y tareas de interfaz e integración. |
| RF-S1-04 | Mostrar primero las sucursales más cercanas con disponibilidad. | HU01, criterio 2 | Falta tarea específica y definición de ubicación/distancia. |
| RF-S1-05 | Modelar Producto, Sucursal e Inventario y cargar datos ficticios. | Plan S1; base de HU14 | #6, #3; cobertura parcial de HU14. |
| RF-S2-01 | Registrar y confirmar un pedido con sus productos y cantidades. | HU04 / PBI-04 | #20, #18, #12; refinar cuenta, carrito y plataforma. |
| RF-S2-02 | Reservar stock y liberarlo al vencer el plazo; notificar a la sucursal. | HU02 / PBI-02 | #21, #18; expiración y notificación requieren detalle. |
| RF-S2-03 | Asignar sucursal considerando stock, distancia y capacidad; gestionar falta de alternativa. | HU03 y HU15 | #9, #18, #12; acordar reglas y desempates. |
| RF-S3-01 | Gestionar preparación y cambios de estado autorizados. | Plan S3; HU05 y HU15 | #16, #22. |
| RF-S3-02 | Mostrar estado e historial e informar cambios al cliente. | HU05 / PBI-05 | #15, #19, #22; notificaciones por detallar. |
| RF-S3-03 | Registrar repartidor, entrega y confirmación final. | HU15 / PBI-15 | #19, #22, #17. |
| RF-S3-04 | Registrar incidencias y soporte básico asociado al pedido. | Plan S3; relación parcial con HU11 | #22; no cubre todavía un chat completo. |

## Historias que requieren refinamiento adicional

- HU14: entradas, salidas y correcciones de inventario; la carga inicial no las implementa.
- HU08: sencillez, asistencia y explicación clara; las pantallas aportan cobertura parcial.
- HU09: alertas por falta de confirmación y reasignación automática.
- HU06, HU07, HU10, HU12 y HU13: conservar en el backlog según su prioridad propuesta; no hay sprint comprometido para su cobertura completa.

## Calidad y reglas que deben validarse

- Búsqueda y filtros coherentes; mensajes de carga, vacío y error comprensibles.
- Stock no negativo y un inventario único por producto y sucursal.
- Las reservas no pueden superar el stock disponible; operaciones concurrentes deben preservar esa regla.
- Los cambios de estado y de inventario requieren permisos cuando se implemente autenticación.
- Impedir entrega duplicada y registrar las transiciones relevantes.
- Usar datos ficticios; demostrar integración mediante pruebas reproducibles.

Autenticación, roles, reportes, ventas de mostrador y alertas de stock mínimo proceden también de la versión histórica. Deben refinarse antes de tratarlos como compromisos adicionales del MVP.

## Validación

[Casos de prueba](../05-pruebas/CASOS_DE_PRUEBA.md) · [Estado y pendientes](../ESTADO_Y_PENDIENTES.md). Ya están registrados los [resultados de la base de datos](../06-evidencias/2026-10-18_base-datos-sprint-1.md); no acreditan la aplicación integrada.
