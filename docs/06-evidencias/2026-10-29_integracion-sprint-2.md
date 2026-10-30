# S2-05 — Integración y revisión del Sprint 2

**Responsable:** Sebastian Calderon. **Issue:** [#12](https://github.com/seale-code/Ingenieria-de-software/issues/12).
**Fecha:** 29 de octubre de 2026 (Perú).
**Base revisada:** `886acb7c7db51858d2a7f1e30c442760e5d3297f` de `main`.
**Implementación probada:** `161e7a983caa9221eb077e1679296ec7d76a5097`
(contenido equivalente al commit local `e877b90`).

## Resultado de ejecución

Python 3.12 / SQLite / Linux, bases temporales independientes y datos ficticios.
Suite inicial del repositorio: **104 pruebas aprobadas**. Los tres nuevos escenarios
de integración reprodujeron **2 fallos y 1 error** antes de la corrección.
Después de integrar, suite completa: **120 pruebas aprobadas, cero fallos/errores**.

```bash
python -m unittest discover -s tests -v
```

- [Salida antes de corregir: tres regresiones](2026-10-29_s2_antes.txt).
- [Salida final completa: 120 pruebas](2026-10-29_s2_resultados.txt).
- [16 casos: datos, pasos y resultados esperados](../05-pruebas/S2-05-casos-prueba-pedidos.md).
- [Guía de ejecución, contrato y compatibilidad](../../sprint-2/S2-05_Sebastian_Calderon.md).

Todos los casos S2-CP-01 a S2-CP-16 resultaron **aprobados** en esta propuesta.
Se verificó en proceso real la CLI de Anderson, sin simular las consultas SQLite ni
las reglas de César. Dos pruebas usan hilos, barrera de inicio y conexiones distintas
para demostrar competencia por una última unidad y por un último cupo.
La reserva se guarda en `reservas_stock`, conserva inventario físico y se descuenta
una sola vez al consumirla. Los errores de persistencia revierten también el historial.

## Defectos reproducidos y corregidos

| ID | Reproducción en main | Esperado / obtenido antes | Corrección y regresión |
|---|---|---|---|
| S2-BUG-01 | Base v3, inicializar módulo, registrar DEMO-A×2. Consultar `pedidos`. | Esperado: pedido y reserva en tablas de Josué. Obtenido: solo tablas provisionales `s2_pedidos`/`s2_reservas`, sin integración con historial/entregas. | Registro v2/v3 usa `pedidos`, `detalles_pedido` y `reservas_stock`; CP-01 y CP-13/14. |
| S2-BUG-02 | Base v3: stock A–Norte=5 y reserva oficial ACTIVA×4; solicitar A×2 por módulo de Anderson. | Esperado: rechazo controlado por disponible=1. Obtenido: sqlite3.IntegrityError al tratar de descontar inventario físico por debajo de lo reservado. | Descontar reservas activas en la evaluación; seleccionar y persistir bajo BEGIN IMMEDIATE; CP-02, CP-09 y CP-12. |
| S2-BUG-03 | Sucursales en el mismo punto e igual capacidad; Norte A×5 y Sur A×10. | Esperado por S2-01: Sur, mayor stock antes del código. Obtenido: Norte por el orden provisional de Anderson. | Reutilizar `asignar_sucursal_pedido` de César en el puente oficial; CP-03. |

## Estado contrastado con GitHub

| Tarea | Evidencia observada | Qué falta |
|---|---|---|
| #9 / César: reglas | PR #34 integrado e Issue cerrado. | Aplicar esas reglas desde el registro: resuelto en esta propuesta. |
| #21 / Josué: modelo | Migraciones v2/v3 y pruebas presentes en main. Issue aún abierto. | Revisar evidencia, aceptar y actualizar el Issue por el equipo. |
| #18 / Anderson: registro | PR #37 integrado; Issue aún abierto. Sus 20 pruebas del modo provisional pasan. | El modo oficial se conecta mediante este PR; revisar y actualizar #18 con la evidencia pertinente. |
| #20 / Willy: formulario | Issue abierto; no se encontró un formulario S2 ni PR que lo implemente en lo revisado. PR #39 es documentación S1-05. | Formulario, resumen, confirmación, errores y conexión al servicio. |
| #12 / Sebastian: integración/pruebas | Esta propuesta agrega el puente y 16 casos con ejecución reproducible. | Revisión de otro integrante y merge; probar el recorrido web cuando exista #20. |

Los PR #35, #36 y #38 de Sebastian para Sprint 1 siguen abiertos al momento de
esta revisión; #36 conecta el catálogo web y #38 aporta su validación. No se hizo
merge de estos PR como parte de S2. El PR #27 de evidencia de BD también seguía abierto.
Los documentos previos y algunas descripciones de Issues siguen indicando
«pendiente» pese a contener código; el nuevo estado del README S2 está respaldado
por esta revisión y no reemplaza la aceptación del equipo.

## Pendientes para cerrar el Sprint 2

1. Revisar y aceptar este PR; revisar/cerrar #18 y #21 con sus evidencias.
2. Implementar y conectar el formulario #20; ejecutar el flujo web completo.
3. Definir cuenta, autenticación/permisos y relación cliente-pedido de HU04.
   El nombre del cliente de esta demostración no es una cuenta autenticada.
4. Acordar duración de reserva, liberación por vencimiento, notificación a sucursal
   y tratamiento de reasignación. La reserva actual no tiene vencimiento automático.
5. Usar disponible tras reservas en la experiencia de compra; el catálogo S1 consulta
   stock físico. La confirmación sí valida disponible en esta propuesta.
6. Conciliar bases de demostración que ya tengan pedidos provisionales antes de
   habilitar escrituras con el modelo oficial. No copiar reservas que ya descontaron
   stock como si fueran reservas nuevas. El módulo bloquea este caso y conserva datos.
7. Registrar Sprint Review, aceptación del incremento y retrospectiva con participantes.

La revisión no acredita una aplicación web de compra terminada ni cobertura completa
de HU02/HU04. No se dispone de la rúbrica completa del curso.
