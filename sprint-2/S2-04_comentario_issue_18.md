### Avance S2-04 — Anderson Delerna

Implementé el módulo backend de **registro de pedidos y asignación de sucursal**. El flujo valida datos, consulta el catálogo e inventario existentes, selecciona una sucursal con stock y capacidad, calcula la distancia geográfica y persiste el pedido con su detalle. Si ninguna sucursal califica, registra `SIN_ASIGNAR` y muestra el motivo. Las operaciones de reserva/descuento de inventario usan transacciones para evitar sobreventa.

**Archivos:**
- `src/backend/pedidos_s2.py`
- `src/backend/asignacion_sucursal.py`
- `src/backend/pedidos_s2_schema.sql`
- `src/backend/pedidos_s2_cli.py`
- `tests/test_pedidos_s2.py`
- `sprint-2/S2-04_Anderson_Delerna.md`
- `sprint-2/S2-04_evidencia_pruebas.txt`

**Pruebas:** 20 pruebas automatizadas superadas en el entorno local de verificación, incluido control de reservas concurrentes y rollback. Adjunté instrucciones y evidencia en la carpeta del sprint. Antes de finalizar, debo repetirlas sobre la rama integrada del equipo.

**Pendiente de coordinación:** Las reglas actuales son provisionales a la espera de S2-01 (#9), y las tablas `s2_*` se aislaron deliberadamente hasta integrar el esquema definitivo de S2-03 (#21). Solicito revisión y comentarios de integración antes de cerrar el issue.

**PR/commit:** [Pegar enlace real una vez publicado].
