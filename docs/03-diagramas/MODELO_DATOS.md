# Modelo de datos conceptual por sprint

[← Documentación](../README.md) · [Base de datos](../../src/database/README.md)

## Sprint 1: catálogo y disponibilidad por sucursal

| Entidad | Datos mínimos previstos | Relación / regla |
|---|---|---|
| Categoría | Identificador, nombre | Una categoría agrupa productos; apoya el filtro del plan S1. |
| Producto | Identificador, nombre, categoría | Un producto puede tener inventario en varias sucursales. |
| Sucursal | Identificador, código único, nombre, latitud y longitud | Una sucursal mantiene inventario de varios productos. |
| Inventario | Producto, sucursal, cantidad de stock | Par producto–sucursal único y cantidad no negativa. |

**Producto 1:N Inventario; Sucursal 1:N Inventario.** La disponibilidad depende del par producto/sucursal; no se usa un único stock global por producto.

El [esquema SQLite](../../src/database/schema.sql) implementa estas cuatro entidades con claves foráneas y stock entero no negativo. Las coordenadas tienen rango validado y son ficticias en la demo. La ubicación del usuario y el cálculo de cercanía siguen pendientes de refinar en HU01.

## Extensiones previstas

| Sprint | Entidades o datos del plan | Pendientes |
|---|---|---|
| 2 | Pedido, DetallePedido, sucursal asignada, reserva de stock | Integridad, concurrencia, plazo de reserva y liberación. |
| 3 | Repartidor, Entrega, HistorialEstado e incidencias asociadas al pedido | Estados, permisos, fechas y reglas de confirmación. |

## Fuente y límite

Fuente: tareas #6 y #3 de S1, #21 de S2 y #19 de S3; [HU14](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf) describe inventario completo, aún sin descomposición suficiente.

Los scripts y datos ficticios están implementados y cubiertos por [24 pruebas](../06-evidencias/2026-10-18_base-datos-sprint-1.md). S1-06 y S1-07 quedan en revisión del equipo; no completan HU14. Categoría 1:N Producto; las claves y restricciones exactas están en el esquema SQL. El [modelo histórico](../00-historico/03-diagramas/MODELO_DATOS.md) se conserva como referencia y no se usa para justificar disponibilidad por sucursal.
