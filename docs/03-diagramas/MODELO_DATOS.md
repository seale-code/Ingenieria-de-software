# Modelo de datos conceptual por sprint

[← Documentación](../README.md) · [Base de datos](../../src/database/README.md)

## Sprint 1: catálogo y disponibilidad por sucursal

| Entidad | Datos mínimos previstos | Relación / regla |
|---|---|---|
| Categoría | Identificador, nombre | Una categoría agrupa productos; apoya el filtro del plan S1. |
| Producto | Identificador, nombre, categoría | Un producto puede tener inventario en varias sucursales. |
| Sucursal | Identificador, nombre y datos de ubicación por definir | Una sucursal mantiene inventario de varios productos. |
| Inventario | Producto, sucursal, cantidad de stock | Par producto–sucursal único y cantidad no negativa. |

**Producto 1:N Inventario; Sucursal 1:N Inventario.** La disponibilidad depende del par producto/sucursal; no se usa un único stock global por producto.

Las coordenadas y la referencia del usuario para cercanía deben definirse al refinar HU01. El esquema SQL y los datos de prueba todavía no existen.

## Extensiones previstas

| Sprint | Entidades o datos del plan | Pendientes |
|---|---|---|
| 2 | Pedido, DetallePedido, sucursal asignada, reserva de stock | Integridad, concurrencia, plazo de reserva y liberación. |
| 3 | Repartidor, Entrega, HistorialEstado e incidencias asociadas al pedido | Estados, permisos, fechas y reglas de confirmación. |

## Fuente y límite

Fuente: tareas #6 y #3 de S1, #21 de S2 y #19 de S3; [HU14](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf) describe inventario completo, aún sin descomposición suficiente.

Este modelo es una guía conceptual. Falta elaborar y validar el diagrama entidad-relación detallado y los scripts antes de cerrar la tarea de modelado. El [modelo histórico](../00-historico/03-diagramas/MODELO_DATOS.md) se conserva como referencia y no se usa para justificar disponibilidad por sucursal.
