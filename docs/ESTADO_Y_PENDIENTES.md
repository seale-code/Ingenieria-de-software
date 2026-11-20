# Estado del producto y decisiones de aceptación

**20 de noviembre de 2026**, base funcional `53b6ff8`, PR #56 integrado, esquema v6. [Índice](README.md) · [Informe técnico](INFORME_TECNICO.md).

## Disponible

Catálogo/carrito comercial, cotización, confirmación con reservas, asignación por stock/capacidad/distancia, preparación, reparto, seguimiento por código, incidencias, vencimientos, reasignación y cancelación sin alternativa, entradas/conteos/salidas de inventario con historial.

La versión integrada tiene [322 pruebas Python/API y 44 recorridos Chromium registrados](06-evidencias/2026-11-16_logistica-sucursales.md). La [validación de esta actualización](05-pruebas/VALIDACION_V6.md) mantiene su propia fecha y resultados.

## Fronteras

| Tema | Estado |
|---|---|
| Identidad | Clave compartida de operador; sin cuentas individuales de empleados/clientes. |
| Ubicación | Centro del distrito y distancia geográfica; sin GPS o ETA de ruta. |
| Atención | Domicilio; adaptación del criterio original de reserva/recojo requiere aceptación. |
| Comunicación | Bandeja/seguimiento; sin SMS, correo, push o chat. |
| Información | Catálogo local con fuentes; sin sincronización comercial interna de Inkafarma. |
| Cobros | Pago al recibir registrado; sin pasarela ni acreditación de pago. |
| UML | 17 diagramas agrupados del objetivo; no acreditan funciones futuras como implementadas. |
| Seguridad | [Análisis ejecutado](08-seguridad/ANALISIS_VULNERABILIDADES.md): 23 controles aprobados, cinco hallazgos abiertos y dos observaciones; correcciones/retest por implementar. |

## Validaciones del equipo

- Registrar Product Owner, Scrum Master, duración/fechas y estimaciones realmente acordadas.
- Completar Review, retrospectiva y Daily con hechos/evidencias. Los commits acreditan integración, no asistencia o reuniones.
- Registrar revisión de criterios y aceptación de adaptaciones; cerrar un Issue por merge no sustituye esa decisión.
- Verificar aceptación docente del agrupamiento: la exigencia original de actividades/secuencia/colaboración por cada HU implicaría 47 diagramas para 15 HU, frente a los 17 actuales.
- Validar usabilidad con destinatarios y acordar operación de producción antes de afirmar SLA o beneficios medidos en la operación real.

[Cierre de sprints](07-scrum/ESTADO_CIERRE_SPRINTS.md) · [Cobertura por criterio](01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md).

Los informes previos no se reescriben para aparentar resultados de otra fecha. El [estado documental anterior](00-historico/estado-anterior-v6/ESTADO_Y_PENDIENTES.txt) conserva el texto publicado antes de esta actualización.
