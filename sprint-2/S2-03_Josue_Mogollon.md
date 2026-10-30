# Entregable S2-03 — Josue Mogollon

**Sprint:** 2 — Registro y asignación de pedidos  
**Issue:** #21 — Modelar pedidos, detalles y reserva de stock  
**Rama de trabajo:** `feature/josue-sprint2-pedidos`  
**Estado de este entregable:** listo para pruebas locales, revisión de otro integrante y Pull Request. **No equivale a aprobación automática del Issue.**

## 1. Objetivo y alcance

Mantener un modelo relacional de pedidos, sus detalles y las reservas del inventario, evitando sobreventa y conservando el stock original del Sprint 1. Los archivos base del modelo ya existen en `main`:

- `src/database/migrations/002_pedidos_reservas.sql`: tablas `pedidos`, `detalles_pedido` y `reservas_stock`; índices, claves foráneas, restricciones y triggers.
- `src/database/schema.sql`: catálogo e inventario del Sprint 1.
- `src/database/migrate_josue.py`: procedimiento para aplicar migraciones v2 y v3.

**El paquete actual no reclama haber creado de nuevo las tablas ya presentes en `main`.** Corrige el cierre de conexiones y permite comprobar las garantías existentes del modelo sin errores de limpieza de ficheros temporales en Windows.

## 2. Cambios de esta rama

| Archivo | Cambio | Motivo |
| --- | --- | --- |
| `src/database/migrate_josue.py` | `contextlib.closing` en la conexión SQLite de migración. | Cerrar de forma explícita tanto cuando la migración termina como cuando rechaza una base ajena. |
| `tests/test_josue_migrations.py` | `contextlib.closing` en las conexiones temporales del `setUp` y de la prueba de bases ajenas. | Evitar `PermissionError: [WinError 32]` al limpiar directorios de pruebas en Windows. |
| `sprint-2/S2-03_Josue_Mogollon.md` | Registro del alcance, criterios de aceptación y validación. | Proporcionar trazabilidad entre el cambio y el Issue #21. |

## 3. Criterios de aceptación del Issue #21

1. **Integridad relacional:** ejecutar `test_conserva_integridad_relacional` y `test_relaciones_cantidad_y_sucursal_protegidas`.
2. **No sobreventa:** ejecutar `test_reserva_valida_y_no_sobreventa` y `test_reservas_no_pueden_superar_stock_si_se_modifica_inventario`.
3. **Transiciones de reserva:** verificar liberación, consumo una sola vez y rechazo de reservas para pedidos cancelados.
4. **Evidencia:** adjuntar en el Pull Request el resultado real de las pruebas ejecutadas en el equipo local y el commit revisado.
5. **Revisión:** solicitar al menos un review de otro integrante antes de hacer merge.

## 4. Comandos de validación (desde la raíz del repositorio)

```powershell
py -m pip install -r requirements.txt
py -m unittest discover -s tests -p "test_josue_migrations.py" -v
py -m unittest discover -s tests -p "test_pedidos_s2.py" -v
py -m unittest discover -s tests -v
```

**Registro de referencia:** durante la preparación del paquete se ejecutaron **12 pruebas de migraciones con resultado OK** en un entorno aislado que reproduce los esquemas SQL v1, v2 y v3 publicados en `main`. Esto **no sustituye** las pruebas en Windows ni la ejecución de toda la suite en la rama de integración.

**Resultado real en el equipo de Josue:** _[Completar tras ejecutar comandos anteriores: fecha, versión de Python, total de pruebas, errores, captura o salida de terminal]._  
**Commit:** _[Completar con SHA del commit]._  
**Revisor:** _[Completar con usuario de GitHub y resultado del review]._

## 5. Riesgos y delimitación

- La migración S2-03 original ya estaba en el repositorio; no duplicar ni volver a ejecutar su SQL manualmente.
- La suite general podría presentar errores de otros módulos: reportar los resultados por separado y comunicar incidencias al responsable.
- Probar siempre sobre archivos SQLite temporales o de demostración; nunca ejecutar migraciones a ciegas sobre una base compartida.
- El Issue #21 figura cerrado en GitHub en la consulta pública realizada el 30-10-2026. El Pull Request debe vincularse con `#21` y pasar revisión; pedir reapertura si el equipo exige el flujo `Closes #21` para cerrar automáticamente.

## 6. Descripción sugerida para el Pull Request

**Título:** `[S2-03] Corregir conexiones SQLite y validar pedidos y reservas`

**Descripción:**

> Se corrige la liberación de conexiones SQLite durante las migraciones y en las pruebas de integridad y reservas del Sprint 2. Se conserva el esquema existente (`pedidos`, `detalles_pedido`, `reservas_stock`) y se documenta la verificación de integridad, transiciones y prevención de sobreventa.
>
> Validación: [colocar aquí resultados REALES de los comandos anteriores].
>
> Referencia: #21. Si el Issue se reabre, incluir `Closes #21` en la descripción del PR.

**Atención:** Este cambio de robustez y sus pruebas pueden respaldar el Issue, pero el cierre final y la aceptación deben ser confirmados por el equipo.
