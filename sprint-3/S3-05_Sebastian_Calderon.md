# S3-05 — Validación del MVP y demostración

Responsable: Sebastian Calderon (`seale-code`). Tarea [#17](https://github.com/seale-code/Ingenieria-de-software/issues/17), en el [Project Inkafarma](https://github.com/users/seale-code/projects/1). Trazabilidad: PBI-05, PBI-15 y soporte parcial PBI-11.

## Ampliación del 12 de noviembre de 2026

El PR #48 ya está integrado, al igual que preparación (#47). Se amplía la validación sobre el seguimiento de Willy (#49, todavía abierto): **211 pruebas Python/API y 24 recorridos Chromium aprobados**. Incluye 6 casos API nuevos, 9 casos de navegador, copia del código de seguimiento y una demo que compara la API pública con el historial real de preparación. [Evidencia actual](../docs/06-evidencias/2026-11-12_seguimiento-validacion-mvp.md).

Queda por completar #22 y repetir el recorrido hasta ENTREGADO; las comprobaciones siguientes del 11 de noviembre se conservan como historial.

## Resultado de la propuesta inicial

Se añadieron 12 pruebas de integración entre catálogo, confirmación, reservas, repartidores e historial, un recorrido de navegador entre catálogo y pedido, y una demostración técnica reproducible. Se detectó y corrigió que el catálogo mostraba stock físico como disponibilidad aun cuando existían reservas activas.

Ejemplo real: DEMO-A tiene 5 unidades en Norte. Confirmar 2 deja inventario físico 5 y disponibilidad 3. Antes, catálogo y detalle mostraban 5. Ahora ambas consultas HTTP muestran 3, y el filtro de disponibles excluye productos agotados por reservas. Consumir una reserva descuenta inventario una vez; liberar la reserva restituye disponibilidad. `get_stock()` conserva su comportamiento físico para los consumidores existentes; el parámetro `effective=True` habilita el cálculo efectivo, compatible con v1/v2/v3.

## Validación realizada

| Configuración | Resultado |
|---|---|
| Nuevos casos sobre main, antes de corregir | 12 casos: 4 fallos por disponibilidad obsoleta |
| Main `06211a6103c316483d866da2e103bddfe0df47f0` + propuesta | 187 pruebas Python/API aprobadas |
| Navegador sobre propuesta | 8 casos catálogo y 7 pedidos aprobados; los primeros 14 también se ejecutaron juntos |
| Main + PR #47 `4968c063b8c287705554343d262e7ce564ab275a` + propuesta | 198 pruebas Python/API aprobadas |
| Demo técnica sobre main + propuesta | Registro, reserva, disponibilidad, relación con repartidor y fechas comprobados |
| Demo con PR #47 integrado localmente | Además, ASIGNADO → EN_PREPARACION → PREPARADO e historial comprobados |

La rama de #47 era anterior a #46. Para la validación compuesta se fusionó `origin/main` en un worktree local de #47 y se aplicó esta propuesta; ninguna rama remota se fusionó. Las cantidades anteriores no deben sumarse como casos distintos.

[Casos](../docs/05-pruebas/S3-05-validacion-mvp.md) · [Logs y defectos](../docs/06-evidencias/2026-11-11_validacion-mvp-sprint-3.md) · [Demo](DEMO_MVP.md).

## Dependencias registradas el 11 de noviembre (ver actualización anterior)

- #16 / PR #47: revisión e integración de preparación; faltan pantallas para el personal en main.
- #15: seguimiento del pedido para el cliente todavía sin interfaz/endpoint en main revisado.
- #22: transiciones de reparto, permisos e incidencias aún pendientes. Registrar fechas con S3-03 no cambia el pedido a EN_CAMINO/ENTREGADO ni la entrega a EN_CAMINO/ENTREGADA. No se sustituyeron esos servicios mediante actualizaciones SQL en la demo.
- Repetir el recorrido completo con esos cambios, comprobar cierre/consumo de reservas según la política acordada y obtener revisión de otro integrante.

No se asigna una implementación a otro integrante ni se cierran sus tareas desde esta propuesta.

## Aceptación

- [x] Preparar y ejecutar validación de los componentes disponibles.
- [x] Corregir el defecto de disponibilidad y añadir regresión HTTP y navegador.
- [x] Adjuntar logs, diagnóstico y guion reproducible.
- [ ] Validar el recorrido completo hasta ENTREGADO con seguimiento y soporte.
- [ ] Obtener revisión del equipo y registrar aceptación del MVP.

El merge de #48 cerró automáticamente #17. La ampliación documenta por separado la validación de seguimiento y la dependencia restante #22; el cierre por merge no acredita la aceptación del recorrido completo. No se inventan reuniones, participantes ni resultados de aceptación.
