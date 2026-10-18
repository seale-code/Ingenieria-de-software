# Priorización del Product Backlog

[← Guía Scrum](README.md) · [Backlog ordenado](PRODUCT_BACKLOG.md)

## Método propuesto: MoSCoW

| Categoría | Criterio aplicado al proyecto | PBI |
|---|---|---|
| Must have | Necesario para demostrar el flujo principal: disponibilidad confiable → pedido → reserva/asignación → seguimiento y entrega. | 14, 01, 04, 02, 03, 15, 05 |
| Should have | Mejora importante de continuidad y facilidad de uso; se refina después de asegurar el flujo principal. | 09, 08, 11 |
| Could have | Aporta comodidad o comparación, pero el flujo básico puede demostrarse sin ello. | 07, 06, 10 |
| Won't have en este MVP propuesto | Se conserva para otra versión por dependencias o alcance adicional sin tareas comprometidas. | 12, 13 |

Clasificación propuesta para validación del equipo/Product Owner; no sustituye una decisión de alcance aprobada.

## Por qué ese orden

1. **Inventario (PBI-14) y disponibilidad (PBI-01):** sin datos confiables, las consultas, reservas y asignaciones podrían ofrecer stock inexistente. S1 empieza por su base de datos y consulta.
2. **Pedido digital (PBI-04), reserva (PBI-02) y asignación (PBI-03):** convierten la consulta en una solicitud atendible. S2 depende de productos y stock de S1.
3. **Entrega (PBI-15) y seguimiento (PBI-05):** permiten completar y observar el resultado del pedido en S3.
4. **Continuidad y asistencia (PBI-09, 08, 11):** se refinan según valor y capacidad, conservando legibilidad y mensajes claros desde la interfaz inicial.
5. **Comparación, reposición e historial (PBI-07, 06, 10):** amplían la experiencia tras asegurar el flujo básico.
6. **Multicanal y alternativas (PBI-12, 13):** requieren capacidades adicionales que no están comprometidas en las tareas actuales.

La prioridad de producto no es el orden exacto de programación. Por ejemplo, desarrollar un modelo de datos es una tarea habilitadora; por sí solo no completa la historia de inventario.

## Criterios para revisar prioridades

- Valor para el cliente: encontrar y recibir el medicamento.
- Dependencias: datos → consulta → pedido → reserva/asignación → entrega.
- Riesgo: stock inconsistente, doble reserva, asignación sin capacidad y estados incorrectos.
- Esfuerzo y capacidad disponibles: pendientes de estimación por el equipo.
- Evidencia: cambiar prioridades si la revisión o las pruebas revelan problemas.

## Aplicación a los sprints

| Sprint | Selección funcional propuesta | Límites actuales |
|---|---|---|
| 1 | PBI-01 y base técnica de PBI-14; apoyo de interfaz a PBI-08. | Las 12 tareas no cubren aún orden por cercanía ni movimientos completos de inventario. |
| 2 | PBI-04, 02 y 03; parte de asignación de PBI-15. | Refinar cuenta/carrito, plataforma, expiración de reservas, notificaciones y reglas de asignación. |
| 3 | PBI-15 y 05; soporte básico relacionado con PBI-11. | El chat completo y las alertas/reasignación de PBI-09 requieren tareas específicas si se seleccionan. |

No trasladar automáticamente un PBI completo a “Terminado” porque terminó su sprint. Revisar sus criterios originales y registrar pendientes.
