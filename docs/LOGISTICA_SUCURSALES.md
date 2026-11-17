# Coordinación entre sucursales, reservas e inventario

Entrega técnica asociada a [#17](https://github.com/seale-code/Ingenieria-de-software/issues/17). Implementa criterios de HU02, HU03, HU09 y HU14 sobre el recorrido de entrega existente. La aceptación funcional corresponde al equipo; las pruebas acreditan el comportamiento descrito aquí.

## Política operativa

Cada pedido se atiende completo desde una sola sucursal. Se selecciona entre las que tienen todos los productos y capacidad, usando las reglas de distancia de S2. La sucursal ve el pedido en la bandeja y acepta su atención al **iniciar la preparación**.

Se adopta un plazo inicial de **15 minutos por asignación**. Hasta la aceptación, las unidades quedan reservadas sin descontarse del stock físico. Una reserva aceptada permanece durante preparación y reparto; el pago al recibir no causa una cancelación por falta de pago anticipado.

| Situación | Resultado |
|---|---|
| Aceptación antes del límite | Se registra `aceptada_en` junto con `EN_PREPARACION`; deja de participar en vencimientos automáticos. |
| Llega el instante límite sin aceptación | El supervisor registra la incidencia y busca otra sucursal. |
| La sucursal declara que no puede atender, antes de terminar la preparación | La acción **La sucursal no puede atender → Buscar otra sucursal** registra el motivo y ejecuta la misma búsqueda. |
| Hay una alternativa con stock completo y capacidad | Se liberan las reservas anteriores, se cambia de sucursal y se reservan todas las líneas en el destino. El destino recibe un plazo nuevo. |
| Ninguna alternativa puede atender | Se cancela el pedido, se liberan sus reservas y se registra la solución de la incidencia. El seguimiento informa la causa operativa sin publicar el motivo interno. |
| El pedido ya está preparado, en camino o cerrado | La reasignación queda bloqueada; se conserva el flujo de soporte y cancelación permitido para ese estado. |

No se vuelve a una sucursal ya intentada para el mismo pedido. Esto evita ciclos de reasignación cuando varias sucursales no confirman. Una incidencia general puede registrarse para seguimiento; declarar incapacidad de atención es una acción explícita y con efecto sobre las reservas.

La reasignación conserva ID, código privado, cliente, dirección, productos, cantidades y precios confirmados. Se actualizan la sucursal y su distancia. El cliente consulta el mismo código y ve los cambios de sucursal en el seguimiento.

## Consistencia y concurrencia

`BEGIN IMMEDIATE` abarca liberación, evaluación, incidencia, historial, cambio de sucursal y nuevas reservas. Si falla cualquier escritura, todo se revierte. Se guardan las reservas históricas liberadas; la base permite una sola reserva activa o consumida por línea.

Cada acción de incapacidad de atención lleva un UUID y el ID de asignación que estaba viendo el operador. Repetir el mismo UUID no rechaza también la siguiente sucursal. Una pantalla con una asignación anterior no puede aceptar o completar la preparación del nuevo destino. La competencia por el último stock se resuelve bajo el bloqueo de escritura.

## Inventario

El panel muestra **físico**, **reservado** y **disponible**, donde disponible = físico − reservas activas.

| Movimiento | Efecto | Control |
|---|---|---|
| Apertura | Documenta el saldo existente al migrar o crear una existencia. | Un saldo inicial por producto y sucursal; no vuelve a cargar stock al reiniciar. |
| Entrada | Suma las unidades recibidas. | Cantidad entera positiva, motivo y UUID. |
| Ajuste | Establece el conteo físico final. | Exige el saldo físico que revisó el operador; rechaza un conteo obsoleto o menor a las unidades reservadas. |
| Salida de pedido | Descuenta la cantidad reservada al iniciar el reparto. | Ligada a la reserva consumida; una sola salida por reserva aunque se repita el despacho. |

Registrar el movimiento y actualizar el saldo forman una misma transacción mediante triggers. Se conservan saldo anterior, saldo nuevo, variación, motivo, rol, actor cuando está disponible y fecha. Los movimientos no se editan ni se eliminan. Una corrección posterior se registra como otro ajuste.

Los servicios admiten administración o personal de su propia sucursal. La API del panel determina el rol en el servidor y exige sesión, origen válido y CSRF. El panel conserva su acceso de operador mediante clave compartida: ese mecanismo no atribuye acciones a una identidad individual de empleado. Las salidas automáticas se registran como sistema.

## Ejecución y migración

```bash
python -m scripts.iniciar_tienda
# Cambiar únicamente el plazo de asignaciones futuras:
python -m scripts.iniciar_tienda --reserva-minutos 30
```

Este arranque migra a v6 e inicia el supervisor: revisa inmediatamente y luego cada 30 segundos. No depende de visitas al sitio ni de un temporizador del navegador. El proceso debe estar funcionando para aplicar vencimientos. Al reiniciarse, procesa los plazos vencidos conservados en la base. Varias instancias no duplican la resolución de una asignación.

Para un despliegue con WSGI y planificación externa, ejecutar cada minuto:

```bash
python -m scripts.procesar_reservas --db data/inkafarma-comercial.sqlite3
```

Cada lote procesa hasta 100 pedidos y vuelve a validar su asignación bajo bloqueo. El botón **Revisar vencimientos** permite ejecutar un lote desde una sesión del panel. Las consultas GET no modifican pedidos ni inventario.

La migración `006_logistica_inventario.sql` reconstruye las reservas conservando IDs, estados y fechas. Cambia la relación con la sucursal para admitir reservas históricas de destinos anteriores; los triggers exigen que una nueva reserva pertenezca a la sucursal vigente. No se desactivan claves foráneas. Las asignaciones pendientes anteriores reciben el plazo completo desde la migración; las ya aceptadas no se vencen automáticamente. La migración no repone existencias ni genera salidas retroactivas: crea un saldo de apertura verificable.

## API del panel

Todas estas rutas requieren una sesión habilitada. Cada POST exige JSON y `X-CSRF-Token`.

| Método y ruta | Operación |
|---|---|
| `GET /api/demo/pedidos/<id>` | Incluye control de aceptación e historial de sucursales en `logistica`. |
| `POST /api/demo/pedidos/<id>/acciones` | `preparar` y `listo` exigen `asignacion_id` en v6. `rechazar` exige además `motivo` y `solicitud_id` UUID. |
| `POST /api/demo/reservas/procesar` | Ejecuta un lote con cuerpo `{}` y devuelve cuántos pedidos se procesaron. |
| `GET /api/demo/inventario` | Existencias y hasta 100 movimientos recientes. |
| `POST /api/demo/inventario/movimientos` | Producto, sucursal, `ENTRADA` o `AJUSTE`, cantidad, motivo, UUID; el ajuste añade `cantidad_esperada`. |

Los conflictos de negocio responden 409; los fallos de persistencia responden 503 con un mensaje genérico. La API rechaza roles y actores enviados por el navegador. El seguimiento público muestra sucursal, estados y mensajes públicos de reasignación; no expone dirección, teléfono, motivos internos ni identidades de operadores.

## Relación con las historias y la exposición

| Historia | Criterio abordado | Comprobación |
|---|---|---|
| HU02 | Reserva temporal, aviso en bandeja, plazo y liberación. | Pruebas de aceptación, límite exacto, supervisor sin tráfico web y cierre de reservas. Se aplica a pedidos de entrega; la modalidad de reserva para recojo del original requiere aceptación de esta adaptación. |
| HU03 | Otra sucursal si la primera no puede atender. | Conservación del pedido, evaluación de stock completo/capacidad y liberación de origen. |
| HU09 | Detección de falta de aceptación, reasignación automática y solución registrada. | Vencimientos concurrentes, exclusión de sucursales intentadas y cancelación documentada sin alternativa. |
| HU14 | Ingresos, salidas y correcciones autorizadas. | Movimientos, conteo obsoleto, protección de reservas, permisos e idempotencia. |

Para mostrarlo: crear un pedido, declarar falta de atención en Miraflores, comprobar el cambio a San Isidro con el mismo código, preparar y despachar, y abrir Inventario para verificar que solo el destino registró la salida. Registrar luego una entrada y un conteo físico; intentar un conteo menor a las reservas muestra el control de integridad.

Los inventarios y movimientos pertenecen a la base de esta propuesta. No se presenta una conexión con existencias internas de Inkafarma. La ubicación continúa usando el centro del distrito y distancia geográfica; esta entrega no calcula tiempos de ruta ni afirma mejoras de rapidez medidas.

Validación reproducible sin modificar la tienda:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s tests/e2e -v
python -m scripts.validar_logistica
```
