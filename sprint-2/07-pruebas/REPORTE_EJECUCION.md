# Reporte de ejecución y evidencias del Sprint 2

**Fecha de la ejecución informada:** 30/10/2026  
**Ejecutor:** Josue Mogollon (`josue456cris`)  
**Entorno observado:** Windows + PowerShell + Python 3.13 + SQLite  
**Rama:** `feature/josue-sprint2-pedidos`  
**PR de trazabilidad:** [#44](https://github.com/seale-code/Ingenieria-de-software/pull/44)

## 1. Incidencia previa

La ejecución inicial de migraciones reportó errores `PermissionError: [WinError 32]`, con archivos temporales SQLite aún abiertos durante su eliminación en Windows. Se aplicaron correcciones de cierre explícito de conexiones en `src/database/migrate_josue.py` y `tests/test_josue_migrations.py`.

## 2. Resultados recibidos en el registro del integrante

| Ejecución | Comando | Resultado observado |
|---|---|---|
| Migraciones | `py -m unittest discover -s tests -p "test_josue_migrations.py" -v` | **12 pruebas / OK** |
| Pedidos | `py -m unittest discover -s tests -p "test_pedidos_s2.py" -v` | **20 pruebas / OK** |
| **Total parcial** | **32 pruebas específicas** | **32 aprobadas, 0 errores reportados** |

**Límites:** estos dos módulos no equivalen a todas las pruebas del sistema. La salida final de `py -m unittest discover -s tests -v` debe registrarse por separado si se ejecuta.

## 3. Evidencia del repositorio de integración (otro responsable/entorno)

El documento del **29/10/2026** en `docs/06-evidencias/2026-10-29_integracion-sprint-2.md` informa **120 pruebas** aprobadas en Python 3.12 / Linux para la integración de Sebastian Calderon, S2-05. Es una fuente distinta a la verificación Windows de Josue.

## 4. Vinculación a criterios del Issue #21

| Criterio de aceptación | Evidencia disponible | Estado de verificación |
|---|---|---|
| Integridad de relaciones | `test_conserva_integridad_relacional` | Prueba local OK (30/10) |
| No exceder stock disponible | `test_reserva_valida_y_no_sobreventa` + concurrencia | Pruebas locales OK (30/10) |
| Adjuntar evidencias | Registro de 32 tests, PR #44 | Adjuntar capturas/logs si el curso lo exige |
| Revisión por otro integrante | PR #44 abierto en la fecha de consulta | **Pendiente de aprobación/merge** |

## 5. Evidencias adicionales que se recomienda adjuntar

- [ ] Captura de `Ran 12 tests ... OK` (real).
- [ ] Captura de `Ran 20 tests ... OK` (real).
- [ ] Captura o archivo de resultado de suite completa si se ejecuta.
- [ ] Captura de PR #44 con aprobación por revisor.
- [ ] Enlace al merge/commit integrado en `main`.

## 6. Registro para nuevas ejecuciones

| Fecha/hora | Commit probado | Comando | Total | Fallos | Errores | Evidencia adjunta |
|---|---|---|---:|---:|---:|---|
| [Pendiente] | [SHA] | [Comando] | [N] | [N] | [N] | [Ruta o URL] |

**No reemplazar los datos faltantes por resultados inventados.**
