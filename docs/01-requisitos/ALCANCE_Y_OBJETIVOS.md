# Alcance y objetivos

[← Documentación](../README.md) · [Requisitos](REQUISITOS.md)

## Objetivo general

Desarrollar un prototipo académico de gestión de pedidos entre sucursales de Inkafarma que permita consultar productos y disponibilidad, registrar un pedido, asignarlo a una sucursal y seguir su preparación y entrega.

## Objetivos específicos

1. Consultar catálogo, buscar por nombre y filtrar productos.
2. Consultar disponibilidad por sucursal y atender el criterio de cercanía de HU01.
3. Registrar pedidos y gestionar reserva/asignación según stock, distancia y capacidad.
4. Registrar preparación, seguimiento y confirmación de entrega.
5. Validar el flujo mediante pruebas y evidencias de los tres sprints.

## Alcance por sprint

| Sprint | Alcance previsto | Documento |
|---|---|---|
| 1 | Catálogo, búsqueda, filtros y consulta de disponibilidad. Modelo inicial Producto–Sucursal–Inventario. | [Plan S1](../../sprint-1/README.md) |
| 2 | Registro, reserva y asignación de pedidos. | [Plan S2](../../sprint-2/README.md) |
| 3 | Preparación, entrega, seguimiento, soporte básico y validación del MVP. | [Plan S3](../../sprint-3/README.md) |

El modelo inicial de inventario no completa HU14. El plan S1 tampoco contiene aún una tarea explícita de orden por cercanía. Estas brechas se mantienen visibles en el [backlog](../07-scrum/PRODUCT_BACKLOG.md).

## Límites

- Solo sucursales de Inkafarma, con datos ficticios para la demostración académica.
- La cobertura web/móvil y las modalidades de entrega/recojo requieren acuerdo del equipo.
- Pagos reales, SUNAT, integración con inventarios comerciales, recetas y operación regulatoria no forman parte del prototipo previsto.
- Multicanal y alternativas de medicamentos permanecen en el backlog como alcance diferido propuesto.

## Fuente y decisiones abiertas

Fuente funcional: [HU01–HU15](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf). Priorización: [MoSCoW](../07-scrum/PRIORIZACION.md).

Acordar fechas, duración, capacidad, roles Scrum, estimaciones, modalidad de entrega y criterios de aceptación pendientes. La propuesta técnica conversada es Flask/Python, SQLite y HTML/CSS/JavaScript; SQLite ya está implementado y probado; Flask y la interfaz siguen pendientes.

La [versión anterior](../00-historico/01-requisitos/ALCANCE_Y_OBJETIVOS.md) se conserva como referencia.
