# 7. Pruebas y evidencias — Sprint 02

## Objetivo de calidad

Demostrar que el modelo, registro y asignación de pedidos conserva integridad y no asigna más unidades que las disponibles, incluso en casos de concurrencia.

## Fuentes de evidencia separadas

| Evidencia | Contexto | Interpretación |
|---|---|---|
| **12/12** | Pruebas `test_josue_migrations.py` ejecutadas por Josue en Windows el 30/10/2026 | Evidencia local de migraciones, relaciones y reservas. |
| **20/20** | Pruebas `test_pedidos_s2.py` ejecutadas por Josue en Windows el 30/10/2026 | Evidencia local del módulo de pedidos. |
| **120 pruebas** | Documento del proyecto sobre la integración S2-05, ejecutadas en Linux el 29/10/2026 | Resultado de otro entorno y responsable; no atribuir a Josue. |

No se documenta como **aprobada** una ejecución del formulario web ni de toda la suite local hasta adjuntar su salida real.

📄 [Casos de prueba de Sprint 2](CASOS_DE_PRUEBA_S2.md)  
📄 [Reporte y evidencias registradas](REPORTE_EJECUCION.md)

**Referencias del repositorio:** [`tests/`](../../tests/), [evidencia de integración del 29/10](../../docs/06-evidencias/2026-10-29_integracion-sprint-2.md), [PR #44](https://github.com/seale-code/Ingenieria-de-software/pull/44).
