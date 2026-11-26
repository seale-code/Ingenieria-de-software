# Product Backlog — Inkafarma

[← Guía Scrum](README.md) · [Criterios de priorización](PRIORIZACION.md) · [Selección Sprint 1](SPRINT_BACKLOG_1.md)

## Identificación y fuentes

Cada fila es un **PBI**, identificado como PBI-01 a PBI-15 y relacionado con HU01 a HU15 respectivamente. El orden de la tabla es el orden propuesto del backlog, no el número de historia.

Fuente: [Historias de usuario originales](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf), página indicada en cada fila. Los criterios siguientes son resúmenes; para aceptar la historia completa se debe revisar el texto original.

Se adapta “boticas” a **sucursales de Inkafarma**, de acuerdo con el alcance del repositorio. Las prioridades siguen siendo una propuesta para validación. El estado actual por criterio está en la [matriz de implementación v6](../01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md). Una tarea técnica relacionada no demuestra que el PBI esté terminado.

## Lista ordenada

| Orden | PBI / historia / página | Necesidad y valor | Aceptación resumida | MoSCoW | Relación con el plan actual |
|---|---|---|---|---|---|
| 1 | PBI-14 · HU14 · p. 15 | Como administrador, mantener inventario correcto para ofrecer disponibilidad confiable. | Descontar salidas por venta, aumentar stock por ingreso y permitir corrección autorizada. | Must | S1: modelo #6, #3; S2: reservas #21; ampliación de #17: entradas, ajustes y salidas con registro de saldos, permisos e idempotencia. Ver [logística v6](../LOGISTICA_SUCURSALES.md). |
| 2 | PBI-01 · HU01 · p. 2 | Como paciente, consultar disponibilidad para encontrar dónde adquirir el medicamento. | Buscar por nombre; mostrar sucursales con stock, ordenadas por cercanía; informar falta de disponibilidad. | Must | S1: #5, #10 y tareas de interfaz, filtros, datos y pruebas. Falta tarea explícita de orden por cercanía. |
| 3 | PBI-04 · HU04 · p. 5 | Como usuario con poco tiempo, seleccionar productos y confirmar un pedido digital. | Con cuenta registrada, agregar productos al carrito; confirmar pedido; recibir información de entrega. | Must | S2: #20, #18, #12. Carrito y checkout comercial integrados en #55; cuenta de cliente pendiente. Ver cobertura por criterio. |
| 4 | PBI-02 · HU02 · p. 3 | Como cliente, reservar un producto para asegurar disponibilidad al llegar. | Bloqueo temporal de stock, notificación a sucursal y liberación al vencer el plazo sin compra. | Must | S2: #21, #18; ampliación de #17: bandeja, plazo de aceptación de 15 min, supervisor y liberación/reasignación. Adaptación a entrega documentada; el criterio original de recojo requiere validación del equipo. |
| 5 | PBI-03 · HU03 · p. 4 | Como usuario, obtener una sucursal conveniente para atender el pedido. | Evaluar distancia y stock; priorizar la opción conveniente; ofrecer otra si no puede atender. | Must | S2: #9, #18, #12; ampliación de #17: otra sucursal con stock completo y capacidad, conservando pedido e importes. Distancia geográfica entre centros de distrito y sucursales. |
| 6 | PBI-15 · HU15 · p. 16 | Como usuario, recibir el medicamento mediante una asignación y entrega eficientes. | Asignar con disponibilidad, distancia y capacidad; actualizar estados y registrar confirmación de entrega. | Must | S2: #9, #18; S3: #16, #19, #22, #17. Faltan métricas para afirmar rapidez. |
| 7 | PBI-05 · HU05 · p. 6 | Como cliente, conocer el estado del pedido y cuándo estará disponible. | Mostrar estado actual; notificar cambios; avisar cuando esté listo para recoger. | Must | S3: #15, #19, #22, #17. Seguimiento por consulta implementado; sin avisos externos ni modalidad de recojo. |
| 8 | PBI-09 · HU09 · p. 10 | Como administrador, detectar riesgo de cancelación y mantener la atención. | Alertar falta de confirmación de stock; reasignar si hay alternativa; registrar solución y estado. | Should | #9, #18, #22 y ampliación de #17: pendientes en bandeja, vencimiento automático, historial de sucursales e incidencia resuelta con resultado de reasignación/cancelación. |
| 9 | PBI-08 · HU08 · p. 9 | Como adulto mayor, realizar pedidos con una interfaz sencilla y asistencia. | Opciones simples; acceso a ayuda; confirmación con explicación clara. | Should | S1: #4, #7 como apoyo de interfaz; asistencia y validación de uso requieren refinamiento. |
| 10 | PBI-11 · HU11 · p. 12 | Como usuario, resolver dudas durante la compra mediante soporte. | Escribir consulta y recibir respuesta; consultar estado; derivar a asesor cuando corresponda. | Should | S3: #22 contempla soporte básico; no equivale todavía al chat completo descrito en HU11. |
| 11 | PBI-07 · HU07 · p. 8 | Como comprador, comparar opciones disponibles. | Mostrar precios y disponibilidad de forma clara; iniciar compra al seleccionar una opción. | Could | #55 incorpora precios, fichas, orden y carrito; adaptación a comparación entre sucursales de la misma propuesta. |
| 12 | PBI-06 · HU06 · p. 7 | Como paciente, recibir aviso cuando un producto agotado vuelva a tener stock. | Registrar alerta, notificar reposición y permitir continuar la compra. | Could | Sin sprint comprometido; depende de inventario actualizado y notificaciones. |
| 13 | PBI-10 · HU10 · p. 11 | Como usuario frecuente, consultar y repetir compras anteriores. | Ver pedidos previos; volver a agregar productos; proteger datos personales. | Could | Sin sprint comprometido; el historial técnico de estados #19 no sustituye esta historia. |
| 14 | PBI-12 · HU12 · p. 13 | Como cliente, continuar la compra entre canales físicos y digitales. | Información actualizada en ambos canales; conservar datos del pedido al cambiar; mostrar opciones. | Won't en este MVP propuesto | Sin tareas comprometidas de integración entre canales; requiere alcance adicional. |
| 15 | PBI-13 · HU13 · p. 14 | Como paciente, conocer posibles alternativas cuando no exista stock. | Mostrar alternativas e información básica; registrar selección como nuevo pedido. | Won't en este MVP propuesto | Sin tareas comprometidas; el original exige distinguir alternativas y evitar sustituciones médicas automáticas. |

Los números #N corresponden a [Issues de este repositorio](https://github.com/seale-code/Ingenieria-de-software/issues). Para enlaces directos a las tareas de S1, ver [Sprint Backlog 1](SPRINT_BACKLOG_1.md).

## Refinamiento antes de comprometer trabajo

- Validar las prioridades con quien asuma Product Owner y el equipo.
- Dividir historias amplias en partes verificables, manteniendo su HU de origen.
- Estimar esfuerzo con el equipo; no se asignan puntos sin esa conversación.
- Definir responsables de aceptación, fechas y capacidad de cada sprint.
- Resolver los criterios sin tarea asociada antes de afirmar que una historia está cubierta.
- Mantener los PBI Should/Could/Won't en el backlog: postergarlos no elimina la necesidad original.

“Must” expresa importancia para el MVP propuesto; **no implica que las tareas actuales ya cubran toda la historia ni que exista un compromiso de entrega aprobado**.

## Avance técnico del Sprint 1

La base de PBI-14 se entregó con 24 pruebas aprobadas, pendiente de revisión del equipo en esa fecha. Los movimientos y la integración no formaban parte de esa entrega. [Evidencia histórica](../06-evidencias/2026-10-18_base-datos-sprint-1.md).

## Ampliación funcional después del Sprint 3

La versión 6 incorpora coordinación de sucursales, plazos de aceptación y movimientos de inventario vinculados a #17. [Reglas, alcance y criterios comprobados](../LOGISTICA_SUCURSALES.md). Esta actualización describe implementación y verificación técnica; no registra aprobación del Product Owner ni cambia retrospectivamente los compromisos de los sprints.

## Consolidación DOC-01 (#60)

Se conserva el orden MoSCoW y los compromisos históricos. Los estados siguientes cuentan criterios de la matriz v6, no historias aceptadas. Las notas incorporan la remediación del PR #57.

| PBI / HU | Implementado | Adaptado | Parcial | Pendiente |
|---|---:|---:|---:|---:|
| PBI-01 / HU01 | 2 | 0 | 0 | 1 |
| PBI-02 / HU02 | 0 | 3 | 0 | 0 |
| PBI-03 / HU03 | 1 | 2 | 0 | 0 |
| PBI-04 / HU04 | 2 | 0 | 1 | 0 |
| PBI-05 / HU05 | 1 | 0 | 2 | 0 |
| PBI-06 / HU06 | 0 | 0 | 0 | 3 |
| PBI-07 / HU07 | 2 | 1 | 0 | 0 |
| PBI-08 / HU08 | 1 | 0 | 2 | 0 |
| PBI-09 / HU09 | 2 | 1 | 0 | 0 |
| PBI-10 / HU10 | 0 | 0 | 1 | 2 |
| PBI-11 / HU11 | 0 | 0 | 1 | 2 |
| PBI-12 / HU12 | 0 | 0 | 2 | 1 |
| PBI-13 / HU13 | 0 | 0 | 0 | 3 |
| PBI-14 / HU14 | 1 | 2 | 0 | 0 |
| PBI-15 / HU15 | 2 | 1 | 1 | 0 |

HU02/HU04: verificación telefónica previa a la reserva; HU02/HU09: límite total de asignaciones pendientes de 45 minutos; HU14: cuentas personales y auditoría de operaciones. Estos controles no sustituyen los criterios originales de recojo, cuenta de cliente ni venta física. Ver [historias actualizadas](../02-historias-usuario/HISTORIAS_ACTUALIZADAS.md) y [Remediación](../08-seguridad/REMEDIACION.md). DOC-01–DOC-09 se agrupan en #59; no constituyen un Sprint 4 aprobado.
