# PBI seleccionados y criterios de aceptación del Sprint 2

**Fuente de referencia:** [Product Backlog oficial](https://github.com/seale-code/Ingenieria-de-software/blob/main/docs/07-scrum/PRODUCT_BACKLOG.md). Los criterios siguientes son una **descomposición operativa propuesta** para el Sprint 2; no reemplazan el texto de las historias de usuario originales.

## PBI-04 / HU04 — Confirmación de un pedido

**Necesidad:** un usuario desea seleccionar productos y confirmar un pedido digital.

- **CA-S2-01:** dados productos válidos y cantidades enteras positivas, el sistema permite iniciar un registro de pedido.
- **CA-S2-02:** el pedido conserva referencia a sus productos y cantidades.
- **CA-S2-03:** si los datos son inválidos, se notifica el motivo y no se generan reservas parciales.
- **Pendiente de alcance:** cuenta registrada, carrito e interfaz web completa no quedan acreditados con una operación de consola.
- **Tareas:** [S2-02 / #20](https://github.com/seale-code/Ingenieria-de-software/issues/20), [S2-04 / #18](https://github.com/seale-code/Ingenieria-de-software/issues/18), [S2-05 / #12](https://github.com/seale-code/Ingenieria-de-software/issues/12).

## PBI-02 / HU02 — Reserva de stock

**Necesidad:** asegurar existencias para atender el pedido, evitando prometer productos ya comprometidos.

- **CA-S2-04:** reservar solo si `stock físico - reservas activas >= cantidad requerida`.
- **CA-S2-05:** si no existe stock suficiente, rechazar reserva sin guardar cambios parciales.
- **CA-S2-06:** una reserva activa conserva trazabilidad con pedido, producto y sucursal.
- **CA-S2-07:** una reserva consumida afecta el inventario físico **una sola vez**; una liberada deja unidades disponibles para nuevas reservas.
- **Pendiente:** establecer vencimiento temporal y notificaciones automáticas; el PBI completo solicita esos comportamientos.
- **Tareas:** [S2-03 / #21](https://github.com/seale-code/Ingenieria-de-software/issues/21), S2-04.

## PBI-03 / HU03 — Elección de sucursal

**Necesidad:** escoger una sucursal que pueda atender el pedido.

- **CA-S2-08:** descartar sucursales sin stock total del pedido.
- **CA-S2-09:** descartar sucursales sin capacidad y aplicar criterios de distancia y desempate definidos por el equipo.
- **CA-S2-10:** si ninguna sucursal es elegible, devolver resultado controlado, sin pedido/reservas incompletas.
- **Tareas:** [S2-01 / #9](https://github.com/seale-code/Ingenieria-de-software/issues/9), S2-04, S2-05.

## PBI-15 / HU15 — Asignación y futura entrega

En **Sprint 2** se aborda la parte de **asignación**. Los estados, preparación, reparto y confirmación de entrega pertenecen al Sprint 3. No afirmar cumplimiento integral del PBI-15 por la asignación del Sprint 2.

## PBI-14 / HU14 — Inventario confiable

Provee una base para calcular disponibilidad. El inventario inicial y la integridad del esquema provienen del Sprint 1; las reservas del Sprint 2 añaden unidades comprometidas. Los movimientos de ingreso, venta y corrección autorizada son requisitos más amplios que aún requieren validación propia.

## Matriz de trazabilidad

| Criterio | Responsable predominante | Artefacto verificable | Prueba sugerida |
|---|---|---|---|
| CA-S2-01 a 03 | Willy / Anderson | Interfaz o servicio + contrato | Pedido válido, cantidad inválida |
| CA-S2-04 a 07 | **Josue** | `src/database/migrations/002_pedidos_reservas.sql` + pruebas | No sobreventa, integridad, liberar/consumir |
| CA-S2-08 a 10 | Cesar / Anderson / Sebastian | Reglas + registro e integración | Distancia, capacidad, sin elegibles |

## Criterios de salida

- [ ] PBI e historias alineados con la persona responsable del Product Owner.
- [ ] No se marca historia completa por solo tener tests de backend.
- [ ] Resultado y defectos enlazados a Issues y Pull Requests reales.
