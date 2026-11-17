# Validación de sucursales, reservas e inventario

**16 de noviembre de 2026.** Base: `main` `72c30fa6fcb433a22ae65e62808b1b0aee833bcc`, con la tienda comercial integrada. Tarea: [#17 — Sebastian Calderon](https://github.com/seale-code/Ingenieria-de-software/issues/17), en [Project Inkafarma](https://github.com/users/seale-code/projects/1).

## Resultado

| Verificación | Resultado | Registro |
|---|---|---|
| Suite Python / API completa | **322 pruebas aprobadas**, 46 nuevas. | [python-tests.txt](logistica-sucursales-2026-11-16/python-tests.txt) |
| Suite Chromium completa | **44 recorridos aprobados**, 6 nuevos. | [chromium-tests.txt](logistica-sucursales-2026-11-16/chromium-tests.txt) |
| Recorrido nuevo con SQLite temporal | Reasignación, entrega, entrada, ajuste, vencimiento e integridad correctos. | [recorrido-logistica.json](logistica-sucursales-2026-11-16/recorrido-logistica.json) |
| Recorrido MVP anterior | Conserva preparación, reparto, soporte, cancelación e integridad. | [recorrido-mvp-anterior.txt](logistica-sucursales-2026-11-16/recorrido-mvp-anterior.txt) |
| JavaScript y diferencias | `node --check` en operaciones, pedido y seguimiento; `git diff --check` correctos. | Comprobación local. |

Las pruebas usan bases temporales y HTTP local. No modifican los datos operativos del usuario ni consultan inventarios internos de Inkafarma. Las advertencias registradas en casos de fallos inyectados son esperadas y se comprueba que no se devuelva éxito.

## Casos de negocio comprobados

| Caso | Evidencia del comportamiento |
|---|---|
| La sucursal no puede atender | Miraflores libera 2 unidades reservadas; San Isidro reserva 2. Se conservan código, dirección e importes. El detalle mantiene una línea de producto e historial de ambas sucursales. |
| Despacho del pedido reasignado | Miraflores conserva sus 18 unidades físicas; San Isidro pasa de 18 a 16. Repetir o despachar concurrentemente produce una sola salida de inventario. |
| Plazo pendiente | Antes del límite no cambia la asignación; en el instante límite busca una alternativa y concede un plazo nuevo. El supervisor procesa sin visitas al sitio. |
| Pedido aceptado | Iniciar preparación registra aceptación y estado en una transacción. No vence por el paso del tiempo durante preparación o reparto. |
| Sin alternativas | Cancela, libera las reservas y registra la solución; no vuelve a sucursales ya intentadas. El cliente ve la cancelación con el mismo código. |
| Competencia por existencias | Dos pedidos que compiten por las últimas 2 unidades alternativas no sobre-reservan: uno se reasigna y el otro se cancela sin alternativa. |
| Reintentos y pantallas anteriores | Cuatro solicitudes con el mismo UUID generan una sola reasignación/entrada. Un ID de asignación anterior no acepta ni rechaza al nuevo destino. |
| Entradas y ajustes | Entrada de 5: físico 18 → 23. Conteo final de 20: ajuste −3. Con 2 reservadas quedan 18 disponibles; un conteo de 1 se rechaza. |
| Respuesta de inventario perdida | El servidor registra la entrada; al perder la respuesta, el navegador reintenta con el mismo UUID y conserva una única entrada. |
| Fallos parciales | Fallar después de liberar, al reservar destino o al registrar la salida revierte sucursal, reserva, incidencia, inventario, fecha e historial afectados. |
| Migración y reinicio | v5 → v6 preserva reservas, IDs y stock. Un fallo revierte también la reconstrucción y la versión. Reiniciar conserva movimientos, precios y política. |
| Acceso y privacidad | Sesión/CSRF/origen obligatorios para escribir. El navegador no elige rol o actor; el personal se limita a su sucursal en los servicios. El seguimiento oculta contactos y motivos internos. |

También se corrigió la navegación del panel al seguimiento para abrirla en la misma pestaña y se añadió un caso de navegador. La validación de cantidades conserva las restricciones HTML y muestra el mensaje dentro del formulario; se comprobó que un valor inválido no permita revisar ni registrar el pedido.

## Interfaz verificada

Los seis recorridos nuevos comprueban reasignación hasta la entrega, entrada y ajuste de inventario, respuesta perdida, asignación desactualizada, navegación al seguimiento y vistas de 320/390 px sin desbordamiento de la página. El registro de cada resultado se conserva en `chromium-tests.txt`. Esta entrega publica los registros de pruebas sin capturas de pedidos.

## Reproducción

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
python -m scripts.validar_logistica
python -m scripts.validar_mvp
```

Los registros corresponden a Python 3.12, Flask 3.1.3 y Playwright 1.51.0 con Chromium headless shell 1161. En el registro de navegador se omiten las líneas rutinarias del servidor HTTP configurando el logger `werkzeug` a nivel ERROR; se conserva el resultado de cada prueba. Las fechas de interfaz se muestran en hora de Lima.

[Reglas operativas y configuración del supervisor](../LOGISTICA_SUCURSALES.md). La aceptación del equipo y la revisión del PR deben registrarse aparte de esta verificación técnica.
