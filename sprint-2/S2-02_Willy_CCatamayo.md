# S2-02 — Formulario, resumen y confirmación del pedido

Tarea de Willy CCatamayo: [Issue #20](https://github.com/seale-code/Ingenieria-de-software/issues/20).
Estado: implementación y pruebas preparadas para revisión. Cuenta de publicación
verificada en Brave: `WillyCcV19`. La tarea requiere revisión de otro integrante.

## Entrega

- `/pedido`: seleccionar productos, cantidades, nombre ficticio y punto de referencia.
- Agregar/quitar líneas, agrupar productos repetidos y validar cantidades enteras positivas.
- Resumen editable con productos, cantidades y total de unidades. No se inventan precios.
- Confirmación explícita: recién entonces se registra y reserva en la base de datos.
- Resultado con número de pedido, sucursal asignada y estado; errores de datos,
  falta de stock, carga y conexión comprensibles.
- Reintento con el mismo identificador de confirmación para recuperar una respuesta
  perdida sin duplicar pedidos ni reservas; dos POST concurrentes también comparten resultado.
- Diseño responsive, etiquetas asociadas, foco y teclado, aviso de errores y pasos visibles.

## Dependencias y ejecución

La entrega depende de PR #36 (Flask/catálogo de S1) y PR #40 (servicio integrado S2).
Ambos están fusionados en `main`; el parche se aplicó sin conflictos sobre
`6cb0ae2c2f28afdb15766bc3fd757439fe46b69b` el 30 de octubre de 2026.
El código usa las reglas de César y el modelo oficial de reservas de Josué a
través del registro de Anderson adaptado en #40. No modifica credenciales ni cuentas.

Desde la raíz, usando una base nueva de demostración:

```bash
python -m pip install -r requirements.txt
python -m src.database init --demo --db .test-tmp/willy-demo.sqlite3
python -m src.database.migrate_josue --db .test-tmp/willy-demo.sqlite3 --hasta 2
python -m src.backend.pedidos_s2_cli --db .test-tmp/willy-demo.sqlite3 init
```

PowerShell:

```powershell
$env:INKAFARMA_DB = '.test-tmp/willy-demo.sqlite3'
python -m src.backend.app
```

Bash: `INKAFARMA_DB=.test-tmp/willy-demo.sqlite3 python -m src.backend.app`.
Abrir http://127.0.0.1:5000/pedido. También hay acceso desde el catálogo.
Capacidad por defecto: 10 según las reglas existentes. La confirmación web exige
esquema v2/v3; no escribe pedidos en las tablas provisionales de v1.

## Contrato web

| Método | Ruta | Contrato |
|---|---|---|
| GET | `/api/pedidos/opciones` | Productos reales del catálogo y puntos ficticios de referencia de la tabla sucursales. Sin escritura. |
| POST | `/api/pedidos` | JSON: cliente, latitud, longitud, items, confirmacion_id (UUID). Usa el servicio y una transacción SQLite. |

200: pedido registrado o resultado de la misma confirmación recuperado. 400:
datos inválidos. 409: sin alternativa elegible o identificador reutilizado con otros
datos. 503: servicio/base no disponible, sin revelar rutas ni errores internos.
El límite de cuerpo HTTP es 32 KiB. Las respuestas API no se almacenan en caché.
El cliente conserva en memoria el payload y su UUID entre reintentos; una vez
incierto el resultado, bloquea edición y ofrece comprobar la misma confirmación.
Esta recuperación cubre la página abierta; no conserva el pedido al recargar/cerrar.

## Verificación

Implementación local: commit `2cea46c` (y documentación posterior).
**147 pruebas Python/API y 6 recorridos de navegador aprobados.**
Reejecutadas con éxito sobre el `main` indicado el 30 de octubre de 2026.
Incluye 12 pruebas HTTP nuevas y 6 pruebas E2E nuevas; las demás corresponden a
servicios y catálogo de los PR de base. Base temporal y datos ficticios en cada caso.

```bash
python -m unittest discover -s tests -v
python -m pip install playwright==1.51.0
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -p test_pedido_browser.py -v
```

Para guardar capturas: prefijar la última orden con
`EVIDENCE_DIR=.test-tmp/capturas` en Bash, o definir `$env:EVIDENCE_DIR` en PowerShell.

[Registro de pruebas y capturas](../docs/06-evidencias/2026-10-29_formulario-sprint-2.md).

## Límites y aceptación pendiente

El nombre es un dato ficticio de la solicitud, no una cuenta autenticada. Los puntos
son ubicaciones de sucursales como referencias de demostración, no una dirección
real de entrega. No hay pagos, notificaciones, vencimiento automático ni seguimiento
S3 dentro de esta tarea. La disponibilidad se comprueba al confirmar.

- [x] Validar productos y cantidades; mostrar resumen, confirmación y errores.
- [x] Adjuntar evidencia del resultado y de las pruebas aplicables.
- [ ] Publicar el PR desde la cuenta elegida con `Closes #20`.
- [ ] Obtener revisión de otro integrante antes de cerrar la tarea.
