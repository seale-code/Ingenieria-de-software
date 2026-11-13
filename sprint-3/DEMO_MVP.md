# Demostración web del Sprint 3

Actualización: 12 de noviembre de 2026. Tarea [#17](https://github.com/seale-code/Ingenieria-de-software/issues/17). Los PR de preparación (#47), seguimiento (#49) y soporte de Anderson (#52) ya están integrados. Esta ampliación conecta sus servicios a un panel del expositor y comprueba el recorrido hasta **ENTREGADO**.

## Abrir la demostración

Desde la raíz del repositorio, con Python 3.10 o superior:

```bash
python -m pip install -r requirements.txt
python -m scripts.demo_web
```

1. Abre `http://127.0.0.1:5000/` para ver el catálogo.
2. Entra en **Operaciones demo**, o abre `http://127.0.0.1:5000/operaciones`.
3. Copia la **clave de esta demostración** que imprime la terminal e introdúcela en el panel.

El comando crea una base temporal v4, seis productos ficticios, dos repartidores y tres pedidos en distintas etapas. También deja una incidencia de ejemplo. La clave cambia en cada ejecución. Al terminar con **Ctrl+C**, se eliminan estos datos; no se modifica `data/inkafarma.sqlite3`. Si el puerto está ocupado, usa `python -m scripts.demo_web --port 5001`.

El panel está deshabilitado en el arranque habitual `python -m src.backend.app`. La demostración solo escucha en la dirección local `127.0.0.1`.

## Guion para exponer en 4–5 minutos

| Paso | Qué hacer | Qué explicar |
|---|---|---|
| 1. Catálogo | Buscar un producto y consultar stock por sucursal. | La disponibilidad ya considera las reservas activas. |
| 2. Crear pedido | Pulsar **Pedir este producto**, indicar un nombre ficticio, una cantidad y un punto de referencia; revisar y confirmar. | El servidor elige una sucursal por stock, distancia y capacidad. No se realizan cobros. |
| 3. Seguimiento | Copiar el código y abrir el seguimiento en otra pestaña. | El código privado identifica este pedido; el cliente ve estado e historial. |
| 4. Preparación | En el panel, pulsar **Actualizar**, seleccionar el pedido e **Iniciar preparación** → **Marcar como preparado**. | Cada paso agrega su evento al historial. |
| 5. Reparto | Elegir repartidor, **Asignar repartidor** y **Registrar salida**. | Salida, estado, reserva e inventario se guardan juntos. El stock físico se descuenta una vez. |
| 6. Entrega | **Confirmar entrega**, volver a la pestaña del cliente y consultar de nuevo. | Pedido ENTREGADO, entrega ENTREGADA y cinco estados visibles. La consulta se actualiza al pulsar el botón. |
| 7. Soporte | Reportar una incidencia, iniciar su revisión, escribir la resolución y resolverla. | La incidencia conserva su relación con el pedido y la solución documentada. |
| 8. Cancelación | Crear otro pedido y cancelarlo con el diálogo de confirmación antes de la salida. | Las reservas se liberan sin consumir stock; el historial se conserva. |

Los tres pedidos precargados permiten empezar en una etapa intermedia si hay poco tiempo. La bandeja filtra por nombre, número, sucursal y estado. Los contadores resumen los pedidos de toda la base, mientras la bandeja muestra hasta 100 recientes.

## Comprobación técnica reproducible

```bash
python -m scripts.validar_mvp
```

Ejecuta sobre otra base temporal el registro HTTP, reintento de confirmación, preparación, asignación de repartidor, salida y entrega atómicas, reintentos sin doble consumo, seguimiento, resolución de incidencia y cancelación. También comprueba integridad y claves foráneas. Debe devolver `RECORRIDO_TECNICO_MVP_COMPLETO`, los cinco estados y stock físico/disponible coherente.

Para repetir las pruebas:

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
```

[Resultados y capturas](../docs/06-evidencias/2026-11-12_mvp-web-integrado.md).

## Alcance de la demostración

- El expositor tiene una sesión protegida por clave y simula las acciones de sucursal, repartidor y soporte. Esto permite demostrar el proceso; no representa cuentas reales de empleados ni una implementación completa de permisos por usuario.
- El cliente consulta con un código privado. No se incluyen en esa respuesta nombres, coordenadas ni observaciones internas.
- No hay cobros, notificaciones push, rastreo GPS, precios, autenticación completa del cliente ni canales externos. Las coordenadas y los productos son ficticios.
- Tras un error de conexión del panel, pulsa **Actualizar** para comprobar qué se guardó antes de repetir una acción. El registro de incidencias no tiene idempotencia propia.
- El formulario conserva la confirmación incierta en la pestaña actual; no recupera ese borrador tras recargarla.
- La aprobación de la Sprint Review y la revisión por otro integrante se registran cuando el equipo realmente las realice.
