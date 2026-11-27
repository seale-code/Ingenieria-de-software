# Procedimiento de gestión de cambio menor

**Código:** SC-INK-001 · **Versión:** 1.1 · **Proyecto:** Inkafarma · **Issue:** #62

## Objetivo y alcance
Controlar un único cambio de presentación del catálogo, desde su solicitud hasta el cierre. Se excluyen cambios en lógica, base de datos, seguridad, API y reglas de pedidos.

## Roles
| Rol | Responsabilidad | Asignación confirmada |
|---|---|---|
| Solicitante | Registrar necesidad y resultado esperado. | Cesar Milla |
| Responsable de cambios | Revisar integridad, registrar decisión y coordinar evaluación. | Cesar Milla |
| Responsable de aprobación | Aprobar o rechazar con justificación antes de implementar. | `josue456cris` (decisión documentada) |
| Desarrollador | Estimar impacto, implementar lo autorizado y registrar commit. | Cesar Milla |
| Revisor / QA | Verificar criterios y documentar resultado. | Cesar Milla |

## Procedimiento previsto
1. Registrar solicitud SC-INK-001 y asociar Issue #62.
2. Evaluar impacto, costo, riesgos, alcance y criterios de aceptación; remitir al aprobador.
3. Registrar decisión. Si se rechaza, justificar y cerrar sin modificar código.
4. Si se aprueba, implementar exclusivamente el ajuste autorizado en una rama y conservar evidencia previa.
5. Ejecutar validación funcional, accesibilidad y revisión visual; si falla, corregir y repetir.
6. Si pasa, registrar resultados, solicitar revisión del PR e integrar según reglas de GitHub.
7. Actualizar registro y cerrar cuando exista aprobación, evidencia y merge.

## Seguimiento de la ejecución real
La solicitud y evaluación fueron elaboradas, se implementó localmente el botón en `docs/62-gestion-cambios`, se obtuvieron capturas y se ejecutó la regresión con 8 pruebas satisfactorias. El 27/11/2026 `josue456cris` documentó su aprobación en el Issue #62, después de la implementación local y la regresión inicial.

**Desviación:** no se acreditó aprobación previa a la implementación. Acción de control: conservar las fechas reales, completar la validación específica, solicitar al revisor que evalúe la desviación y no integrar hasta obtener conformidad y aprobación del PR.

## Control documental
Los cambios de alcance requieren nueva evaluación y autorización. Conservar historial, evidencias y referencias Git. No publicar datos sensibles. El BPMN adjunto representa el procedimiento previsto, no una reconstrucción de la secuencia real. El cierre sigue pendiente.
